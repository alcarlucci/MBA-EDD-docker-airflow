**Laboratório Desafio Final - Airflow no Docker Compose**
# IGTI - MBA Engenharia de Dados - EDD
## Criação de um pipeline de dados que faça a extração dos dados no MongoDB e na API do IBGE e deposite no Data Lake da empresa. Após a ingestão dos dados no Data Lake, o dado tratado e filtrado será disponibilizado em um Database para realização de algumas consultas.
(Airflow com docker-compose; Data Lake: Amazaon S3; Database: Amazon RDS - MySQL)

Prof. Neylson Crepalde @neylsoncrepalde

## 1. Subir o Airflow localmente em uma estrutura de containers, usando docker-compose para utilização mais robusta.
- Clonar repositório: https://github.com/neylsoncrepalde/docker-airflow
- Ambiente utilizado na atividade: Linux Ubuntu (WSL2)

## 2. Criar uma conta free tier na AWS para realização das atividades.
- https://aws.amazon.com/pt/
- Criação de Resource Groups para organizar serviços criados:
  - AWS Resource Groups > Create Resource Group > Tag based:
  - Group name: [rg-mbadados-m01]
  - TAGs:
    - Ambiente: MBA-Dados
    - Projeto: des-final

![image](https://user-images.githubusercontent.com/101406714/193049260-d736ffcc-1652-4a65-a86a-1e1e6e9df52b.png)

## 3. Criar um bucket no serviço Amazon S3 (na conta da AWS).
- Amazon S3 > Buckets > Create bucket:
  - Name: [mba-dados-desfinal]
  
![image](https://user-images.githubusercontent.com/101406714/193050935-1038d322-8b73-44d6-ad9e-1965b3663090.png)

## 4. Criar uma instância RDS de banco de dados relacional de sua escolha (na conta da AWS).
- Amazon RDS > Databases > Create database
  - Engine: MySQL 8.0.28
  - Templates: Free tier
  - Instance identifier: [db-mbadados]
  - username: admin
  - password: <seu_password>
  - Public access: Yes
  - Database port: 3306

![image](https://user-images.githubusercontent.com/101406714/193056691-904e684e-4163-4f06-b41e-a12878758780.png)

- VPC security groups -> Inbound rules -> Add rule:
  - Type: MYSQL/Aurora;
  - Source: Anywhere-IPv4

![image](https://user-images.githubusercontent.com/101406714/193057977-02ff2a0b-9e54-4824-87cc-c6ae13905286.png)

## 5, 6, 7. Construir um pipeline que faz a captura de dados do MongoDB e da API do IBGE e deposita no S3. O pipeline também deve fazer a ingestão na base de dados SQL que estará servindo como DW. Para persistir os dados no DW, você deve ingerir apenas os dados referentes ao público-alvo, a saber, mulheres de 20 a 40 anos.

- abrir a pasta "docker-airflow" em um editor de código (VSCode por ex.)

- editar arquivo docker-compose-CeleryExecutor.yml
  - webserver:
`image: neylsoncrepalde/airflow-docker:2.0.0-pymongo`
  - flower:
`image: neylsoncrepalde/airflow-docker:2.0.0-pymongo`
  - scheduler:
`image: neylsoncrepalde/airflow-docker:2.0.0-pymongo`
  - worker:
`image: neylsoncrepalde/airflow-docker:2.0.0-pymongo`

- abrir o Docker
- carregar ambiente do Docker Compose - rodar comando no terminal:
```
 docker-compose -f docker-compose-CeleryExecutor.yml up -d
```
(para escalar [n] workers adicionar opção: `--scale worker=[n]`)

- código Python da DAG do Pipeline:
  - pasta dags;
  - arquivo des-final.py

- Amazon S3: conectar no S3 na AWS:
  - criar/copiar credenciais de usuário do IAM: IAM > Usuários > Credenciais de segurança
    - access_key_id: <copiar>
    - secret_access_key: <copiar>

- Configurar as Variáveis de Ambiente da DAG no Airflow (credenciais/passwords):
  - Airflow -> Admin -> Variables

![image](https://user-images.githubusercontent.com/101406714/193074397-3e2ca450-0651-43fc-b181-96aee689d783.png)

- Amazon RDS: conectar no MySQL na AWS:
  - sqlalchemy com MySQL - instalar módulo/driver do MySQL

    `pip install mysqlclient` (windows)
    
    `sudo apt-get install -y python3-mysqldb` (ubuntu)

- executar o Pipeline no Airflow (webserver)
  - http://localhost:8080/

**Graph View**
![image](https://user-images.githubusercontent.com/101406714/193076186-08ce3509-ee97-4c3f-8050-6af3480460ea.png)
**Gantt**
![image](https://user-images.githubusercontent.com/101406714/193076739-0d094528-5b1a-4f96-a020-a0ea5bab730a.png)
**Arquivos no Amazon S3**
![image](https://user-images.githubusercontent.com/101406714/193077662-af60d9ca-a454-4114-90f0-f6e33ca9a8cf.png)

**Database no Amazon RDS - MySQL**
![image](https://user-images.githubusercontent.com/101406714/193079564-f8ae01c2-ae67-42a9-8539-a185c38d32f4.png)

## Encerrar o ambiente do Airflow no Docker Compose:
- Rodar comando no terminal:
```
docker-compose -f docker-compose-CeleryExecutor.yml down
```

##
**André Carlucci**
