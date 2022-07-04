from airflow.operators.bash import BashOperator
from airflow import DAG
import datetime
import pendulum

PATH = "/Users/chenjianfu/Library/Mobile\ Documents/com~apple~CloudDocs/Appwork\ school/personal_project"

default_args = {
  'owner': 'jeff',
  'email': ['s9012126000@gmail.com'],
  'email_on_failure': False,
  'email_on_retry': False,
  'retries': 3,
  'retry_delay': datetime.timedelta(seconds=30)
}

with DAG(
        dag_id='hotel_pipline',
        schedule_interval='00 12 * * *',
        start_date=pendulum.datetime(2022, 7, 4, tz='Asia/Taipei'),
        catchup=False,
        default_args=default_args,
        dagrun_timeout=datetime.timedelta(minutes=600)
) as dag:

    store_last_data = BashOperator(
        task_id='store_last_data',
        bash_command=f"cd {PATH}/data_clean/ && python3 data_transfer.py",
        do_xcom_push=False,
        dag=dag
    )

    hotels_crawler = BashOperator(
        task_id='hotels_crawler',
        bash_command=f"cd {PATH}/crawler/ && python3 hotels.py",
        do_xcom_push=False,
        dag=dag
    )

    booking_crawler = BashOperator(
        task_id='booking_crawler',
        bash_command=f"cd {PATH}/crawler/ && python3 booking.py",
        do_xcom_push=False,
        dag=dag
    )

    agoda_crawler = BashOperator(
        task_id='agoda_crawler',
        bash_command=f"cd {PATH}/crawler/ && python3 agoda.py",
        do_xcom_push=False,
        dag=dag
    )

    data_clean = BashOperator(
        task_id='data_clean',
        bash_command=f"cd {PATH}/data_clean/ && python3 hotels_clean.py",
        do_xcom_push=False,
        dag=dag
    )

    store_last_data >> hotels_crawler >> [booking_crawler, agoda_crawler] >> data_clean