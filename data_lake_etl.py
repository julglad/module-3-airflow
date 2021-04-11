from datetime import timedelta, datetime
from random import randint

from airflow import DAG
from airflow.contrib.operators.dataproc_operator import DataProcHiveOperator

USERNAME = 'ygladkikh'

default_args = {
    'owner': USERNAME,
    'start_date': datetime(2013, 1, 1, 0, 0, 0),
    'email': ['agateglad@gmail.com'],
    'email_on_failure': True,    
}

dag = DAG(
    USERNAME + '_data_lake_etl',
    default_args=default_args,
    description='Data Lake ETL tasks',
    schedule_interval="0 0 1 1 *",
)

tasks = {'billing': '''
                    insert overwrite table ygladkikh.ods_billing partition (year='{{ execution_date.year }}') 
                    select *  
                    from ygladkikh.stg_billing where year(created_at) = {{ execution_date.year }};
        ''',
         'issue': '''
                    insert overwrite table ygladkikh.ods_issue partition (year='{{ execution_date.year }}')                    
                    select * 
                    from ygladkikh.stg_issue where year(start_time)) = {{ execution_date.year }};         
          ''',
         'payment': '''
                    insert overwrite table ygladkikh.ods_payment partition (year='{{ execution_date.year }}')                    
                    select *
                    from ygladkikh.stg_payment where year(pay_date) = {{ execution_date.year }};           
          ''',
         'traffic': '''
                    insert overwrite table ygladkikh.ods_traffic partition (year='{{ execution_date.year }}')                    
                    select * 
                    from ygladkikh.stg_traffic where year(from_unixtime(`timestamp` DIV 1000)) = {{ execution_date.year }};            
          '''}

dm_traffic = DataProcHiveOperator(
    task_id='dm_traffic',
    dag=dag,
    query="""
        insert overwrite table ygladkikh.dm_traffic partition (year='{{ execution_date.year }}')
        select user_id, max(bytes_received), min(bytes_received), ceil(avg(bytes_received))
        from ygladkikh.ods_traffic
        where year(created_at) = {{ execution_date.year }}
        group by user_id;
    """,
    cluster_name='cluster-dataproc',
    job_name=USERNAME + '_dm_traffic_{{ execution_date.year }}_{{ params.job_suffix }}',
    params={"job_suffix": randint(0, 100000)},
    region='europe-west3',
)

for task, query in tasks.items():
    ods = DataProcHiveOperator(
        task_id='ods_' + task,
        dag=dag,
        query=query,
        cluster_name='cluster-dataproc',
        job_name=USERNAME + '_ods_' + task + '_{{ execution_date.year }}_{{ params.job_suffix }}',
        params={"job_suffix": randint(0, 100000)},
        region='europe-west3',
    )
    if task == 'traffic':
        ods >> dm_traffic
