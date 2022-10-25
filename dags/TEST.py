import os
from datetime import datetime
from urllib.parse import _ParseResultBase
from airflow.models import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import snowflake.connector
import tempfile

conn = snowflake.connector.connect(
    user='grupods03',
    password='Henry2022#',
    account='nr28668.sa-east-1.aws',
    database='prueba',
    warehouse='dw_prueba',
    schema='public')

def execute_query(connection, query):
    cursor = connection.cursor()
    cursor.execute(query)
    cursor.close()

temp_dir=tempfile.TemporaryDirectory()

def fun_file_to_temp():
    import pandas as pd
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    df=pd.read_csv('https://raw.githubusercontent.com/grupohenryds03/esperanza_vida/main/datasets/Complete.csv')
    df.drop('Unnamed: 0',inplace=True, axis=1)
    df.to_csv(temp_dir +'/EV_completo.csv', index=False)

def fun_file_to_stage():
        sql="remove @DATA_STAGE pattern='.*.csv.gz'"
        execute_query(conn, sql)
        sql = f"PUT file://{temp_dir+'/EV_completo.csv'} @DATA_STAGE auto_compress=true"
        execute_query(conn, sql)
    


with DAG(
    dag_id='file_to_stage_snowflake',
    schedule_interval='@yearly',
    start_date=datetime(year=2022, month=10, day=22),
    catchup=False
    ) as dag:

    task_file_to_temp=PythonOperator(
        task_id='file_to_temp',
        python_callable=fun_file_to_temp)
   
    task_file_to_stage=PythonOperator(
        task_id='file_to_stage',
        python_callable=fun_file_to_stage)

task_file_to_temp >> task_file_to_stage