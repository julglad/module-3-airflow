 
from datetime import timedelta, datetime
from random import randint

from airflow import DAG
from airflow.contrib.operators.dataproc_operator import DataProcHiveOperator

USERNAME = 'ygladkikh'

default_args = {
    'owner': USERNAME,
    'start_date': datetime(2012, 1, 1, 0, 0, 0)
}

dag = DAG(
    USERNAME + '_data_lake_etl',
    default_args=default_args,
    description='Data Lake ETL tasks',
    schedule_interval="0 0 1 1 *",
)

ods_traffic = DataProcHiveOperator(
    task_id='ods_traffic',
    dag=dag,
    query="""
        insert overwrite table ygladkikh.ods_traffic partition (year='{{ execution_date.year }}') 
        select * from ygladkikh.stg_traffic where year(created_at) = {{ execution_date.year }};
    """,
    cluster_name='cluster-dataproc',
    job_name=USERNAME + '_ods_traffic_{{ execution_date.year }}_{{ params.job_suffix }}',
    params={"job_suffix": randint(0, 100000)},
    region='europe-west3',
)
