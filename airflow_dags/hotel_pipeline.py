from airflow.operators.bash import BashOperator
from airflow import DAG
import datetime
import pendulum

PATH = "/home/s9012126000_gmail_com/personal_project"

default_args = {
  'owner': 'jeff',
  'email': ['s9012126000@gmail.com'],
  'email_on_failure': True,
  'email_on_retry': True,
  'retries': 3,
  'retry_delay': datetime.timedelta(seconds=30)
}

with DAG(
        dag_id='hotel_pipline',
        schedule_interval='00 00 * * *',
        start_date=pendulum.datetime(2022, 7, 4, tz='Asia/Taipei'),
        catchup=False,
        default_args=default_args,
        max_active_runs=1,
        dagrun_timeout=datetime.timedelta(minutes=1440)
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

    store_last_data >> hotels_crawler >> booking_crawler, agoda_crawler >> data_clean
