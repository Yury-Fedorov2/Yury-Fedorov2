# dags/weather_dag.py
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Добавляем путь к scripts в PYTHONPATH для импорта функций
SCRIPTS_DIR = '/opt/airflow/project/scripts'
sys.path.insert(0, SCRIPTS_DIR)

from fetch_and_store import fetch_historical, fetch_forecast

# Аргументы по умолчанию
default_args = {
    'owner': 'student',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG
dag = DAG(
    'weather_pipeline',
    default_args=default_args,
    description='Fetch forecast + historical weather',
    schedule='@hourly',  #  ИЗМЕНЕНО: запуск каждый час вместо @daily
    start_date=datetime(2025, 10, 1),
    catchup=False,
)

# Задача 1: получение прогноза
forecast_task = PythonOperator(
    task_id='fetch_forecast',
    python_callable=fetch_forecast,
    dag=dag,
)

# Задача 2: получение исторических данных
historical_task = PythonOperator(
    task_id='fetch_historical',
    python_callable=fetch_historical,
    dag=dag,
)

# Определение зависимостей (опционально, если задачи независимы)
# historical_task >> forecast_task

