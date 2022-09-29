from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash import BashOperator
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import pandas as pd
import json
import pymongo
import boto3
import requests
import os

# Pegar as variaveis de ambiente cadastradas no Airflow
aws_access_Key_id = Variable.get("aws_access_Key_id")
aws_secret_access_key = Variable.get("aws_secret_access_key")
mongo_password = Variable.get("mongo_password")
mysql_password = Variable.get("mysql_password")

# cria um client para o Amazon S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=aws_access_Key_id,
    aws_secret_access_key=aws_secret_access_key
)

# Definir default_args
default_args = {
    "owner": "alcarlucci-MBA",
    "depends_on_past": False,
	"start_date": datetime(2022, 9, 23, 9, 0),
    "email": ["alcarlucci@outlook.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

# Definição da DAG sem usar decorator
# mydag = DAG(
# 	"mba-treino-04",
#     description="MBA-Dados: extração dados ENADE usando PARALELISMO.",
#     default_args=default_args,
#     schedule_interval="*/10 * * * *"  # "At every 10nd minute" - cron expression (https://crontab.guru/)
# )

# Definir a DAG e suas tasks (usando decorator @dag)
@dag(
    default_args=default_args,
    schedule_interval="@once",
    catchup=False,
    description="MBA-Dados EDD - Trabalho Desafio Final",
    tags=["MongoDB", "Python", "EDD", "Postgres", "AWS", "S3", "RDS"]
)
def mba_edd_desafio_final():
    """ 
    Flow para obter dados de uma base MongoDB e API de microrregiões do IBGE;
    e depositar no Datalake no S3 e no DW.
    """
    
    # Extração dos dados do MongoDB
    @task
    def extrai_mongo():
        data_path = "/tmp/pnadc20203.csv"
        client_mongo = pymongo.MongoClient(f"mongodb+srv://estudante_igti:{mongo_password}@unicluster.ixhvw.mongodb.net/ibge?retryWrites=true&w=majority")
        db = client_mongo.ibge
        pnad_coll = db.pnadc20203
        df = pd.DataFrame(list(pnad_coll.find()))
        df.to_csv(data_path, index=False, encoding="utf-8", sep=";")
        return data_path

    # Checagem dos dados extraidos do MongoDB
    @task
    def data_check(file_name):
        df = pd.read_csv(file_name, sep=";")
        print(df)

    # Extração dos dados da API do IBGE
    @task
    def extrai_api_ibge():
        data_path = "/tmp/dimensao_mesorregioes_mg.csv"
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/MG/mesorregioes"
        resp_url = requests.get(url)
        resp_json = json.loads(resp_url.text)
        df = pd.DataFrame(resp_json)[["id", "nome"]]
        df.to_csv(data_path, index=False, encoding="utf-8", sep=";")
        return data_path

    # Escrita no Datalake - upload no Amazon S3
    @task
    def upload_to_s3(file_name):
        bucket_name = "mba-dados-desfinal"
        object_name = os.path.basename(file_name)
        print(f"Got filename: {file_name}")
        print(f"Got object_name: {object_name}")
        print(f"Write on S3 bucket: {bucket_name}")
        s3_client.upload_file(file_name, bucket_name, object_name)

    # Escrita no Postgres (local do container)
    @task
    def write_to_postgres(data_path):
        csv_file = os.path.basename(data_path)
        engine = create_engine("postgresql://airflow:airflow@postgres:5432/airflow")
        df = pd.read_csv(data_path, sep=";")
        if csv_file == "pnadc20203.csv":
            df = df.loc[
                (df.idade >= 20) &
                (df.idade <= 40) &
                (df.sexo == "Mulher")
            ]
        df.to_sql(csv_file[:-4], engine, if_exists="replace", index=False, method="multi", chunksize=1000)

    # ingestão no DW - base de dados MySQL no Amazon RDS
    @task
    def load_to_mysql(data_path):
        csv_file = os.path.basename(data_path)
        engine = create_engine(f"mysql+mysqldb://admin:{mysql_password}@db-mbadados.c8zysqpxouf9.us-east-1.rds.amazonaws.com:3306/mbadados?charset=utf8mb4&binary_prefix=true")
        df = pd.read_csv(data_path, sep=";")
        if csv_file == "pnadc20203.csv":
            df = df.loc[
                (df.idade >= 20) &
                (df.idade <= 40) &
                (df.sexo == "Mulher")
            ]
        df.to_sql(csv_file[:-4], engine, if_exists="replace", index=False, method="multi", chunksize=1000)

    # Task exemplo: DummyOperator
    inicio = DummyOperator(
        task_id="inicio"
    )

    # Task exemplo: BachOperator
    fim = BashOperator(
        task_id="fim",
        bash_command="echo 'Foi pra conta...Fim!'"
    )

    # Orquestração da DAG
    mongo = extrai_mongo()
    api = extrai_api_ibge()

    checagem = data_check(mongo)

    upmongo = upload_to_s3(mongo)
    upapi = upload_to_s3(api)

    wrmongo = write_to_postgres(mongo)
    wrapi = write_to_postgres(api)

    ldmongo = load_to_mysql(mongo)
    ldapi = load_to_mysql(api)
    
    mongo >> checagem >> [upmongo, wrmongo, ldmongo]
    inicio >> [mongo, api]
    [upmongo, upapi, wrmongo, wrapi, ldmongo, ldapi] >> fim

execucao = mba_edd_desafio_final()