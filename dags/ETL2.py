from datetime import datetime
from airflow.models import DAG
from airflow.operators.python import PythonOperator
import snowflake.connector
import tempfile

temp_dir=tempfile.mkdtemp()
conn = snowflake.connector.connect(
    user='grupods03',
    password='Henry2022#',
    account='nr28668.sa-east-1.aws',
    database='prueba',
    warehouse='dw_prueba',
    schema='public',
    insecure_mode=True)

def execute_query(connection, query):
    cursor = connection.cursor()
    cursor.execute(query)
    cursor.close()

def extract_file():
    pass

def file_transform() -> str:
    import pandas as pd
    from sklearn.impute import KNNImputer
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    url='https://raw.githubusercontent.com/grupohenryds03/esperanza_vida/main/datasets/Hechos.csv'
    df=pd.read_csv(url)
    df.drop('Unnamed: 0',inplace=True, axis=1)

    #-----------------------------------------------------

    df.drop_duplicates(inplace = True) # eliminamos las filas duplicadas
    indicadores = df['ID_INDICADOR'].unique()
    indicadores.sort()
    Ind_out = [16] # sacamos el indicador 16 tambien por la redundancia en indicadores
    for i in indicadores:
        x = (df[df['ID_INDICADOR'] == i].VALOR.isnull().sum()/len(df[df['ID_INDICADOR'] == i])) * 100
        if x > 20:
            Ind_out.append(i)
    for i in Ind_out:
        df = df[df['ID_INDICADOR'] != i] # Sacamos los indicadores dentro de Ind_Out

    #-----------------------------------------------------
    imputer = KNNImputer(n_neighbors=2, weights='distance') #Reemplazamos los Valores faltantes con KNNImputer
    after = imputer.fit_transform(df) #Creamos un Data Frame usando 'after' que tiene los datos imputados.
    columnas = df.columns.values
    df_limpio = pd.DataFrame(after, columns=columnas) 

    #-----------------------------------------------------
    df_limpio.ID_PAIS=df_limpio.ID_PAIS.astype(int)
    df_limpio.ID_INCOME=df_limpio.ID_INCOME.astype(int)
    df_limpio.ID_CONTINENTE=df_limpio.ID_CONTINENTE.astype(int)
    df_limpio.ANIO=df_limpio.ANIO.astype(int)
    df_limpio.ID_INDICADOR=df_limpio.ID_INDICADOR.astype(int)
    df_limpio.VALOR=round(df_limpio.VALOR,2)

    #-----------------------------------------------------


    df_limpio.to_csv(temp_dir +'/EV_limpio.csv', index=False)
    sql = f"PUT file://{temp_dir}/EV_limpio.csv @DATA_STAGE auto_compress=true"
    return sql

def file_to_stage(ti) -> None:
    sql=ti.xcom_pull(task_ids='transform')
    execute_query(conn, sql)
    

    
with DAG(
    dag_id='prueba1',
    schedule_interval='@yearly',
    start_date=datetime(year=2022, month=10, day=22),
    catchup=False) as dag:

    extract=PythonOperator(
        task_id='extract',
        python_callable=extract_file,
    )
    transform=PythonOperator(
        task_id='transform',
        python_callable=file_transform,
        do_xcom_push=True
    )

    load=PythonOperator(
        task_id='load',
        python_callable=file_to_stage
    )

    extract >> transform >> load