import os
import pytest
from datetime import datetime, timedelta
import pytz
from src.utils import *

from src.modules.db_manager import CSVHandler

def test_get_yesterday_date():
    """Test que verifica si la fecha de ayer es correcta"""
    colombia_tz = pytz.timezone('America/Bogota')
    now_colombia = datetime.now(colombia_tz)
    expected_yesterday = (now_colombia - timedelta(days=1)).date()
    assert get_yesterday_date() == expected_yesterday

def test_get_yesterday_month():
    """Test que verifica si el mes y año de ayer son correctos"""
    colombia_tz = pytz.timezone('America/Bogota')
    now_colombia = datetime.now(colombia_tz)
    expected_yesterday_month = (now_colombia - timedelta(days=1)).strftime("%m-%Y")
    assert get_yesterday_month() == expected_yesterday_month

def test_get_local_path():
    """Test que verifica si la ruta local generada es correcta"""
    path_without_month = get_local_path(month=False)
    expected_path_without_month = ".\\docs"
    assert path_without_month == expected_path_without_month

    path_with_month = get_local_path(month=True)
    expected_path_with_month = f".\\docs\\{get_yesterday_month()}"
    assert path_with_month == expected_path_with_month

def test_get_cloud_path():
    """Test que verifica si la ruta de la nube generada es correcta"""
    cloud_path_without_month = get_cloud_path(month=False)
    expected_cloud_path_without_month = r"\\192.168.2.20\Contabilidad\REPORTES_BETPLAY"
    assert cloud_path_without_month == expected_cloud_path_without_month

    cloud_path_with_month = get_cloud_path(month=True)
    expected_cloud_path_with_month = r"\\192.168.2.20\Contabilidad\REPORTES_BETPLAY\\" + get_yesterday_month()
    assert cloud_path_with_month == expected_cloud_path_with_month

def test_get_format_month():
    """Test que verifica la fecha indicada de mes con anio"""
    expectative_month, expectative_year = [int(date_for) for date_for in get_yesterday_month().split("-")]
    test_date = get_yesterday_date()
    test_month = test_date.month
    test_year = test_date.year
    assert test_month == expectative_month
    assert test_year == expectative_year

def test_get_month_range_january():
    """Verificar cantidad de dias de este mes"""
    test_date = date(2023, 1, 15)
    assert get_month_range(test_date) == 31

def test_get_month_range_february_non_leap_year():
    """Verificar cantidad de dias de este mes"""
    test_date = date(2023, 2, 15) 
    assert get_month_range(test_date) == 28

def test_get_month_range_february_leap_year():
    """Verificar cantidad de dias de este mes"""
    test_date = date(2024, 2, 15)
    assert get_month_range(test_date) == 29

def test_get_month_range_april():
    """Verificar cantidad de dias de este mes"""
    test_date = date(2023, 4, 15)
    assert get_month_range(test_date) == 30

def test_convert_to_time():
    """Convierte una cadena de texto con 2 formatos posibles en un objeto de tiempo"""
    assert convert_to_time("2025/1/30 10:30:00") == time(10,30,0)
    assert convert_to_time("2025-1-30 12:35:11") == time(12,35,11)
    assert convert_to_time("30-1-2021 2:00:43") == time(2,0,43)
    assert convert_to_time("30/1/2021 20:05:03") == time(20,5,3)
    assert convert_to_time("2025/02/13 12:30") is None
    assert convert_to_time("13-02-2025") is None
    assert convert_to_time("incorrect string") is None

def test_time_compare():
    """Compara 2 tiempos con un umbral definido para saber si son cercanas"""
    assert time_compare(time(1,2,3),time(4,5,6)) == False
    assert time_compare(time(4,5,6),time(1,2,3)) == False
    assert time_compare(time(10,20,00),time(10,21,00), threshold=100) == True
    assert time_compare(time(20,15,6),time(20,15,36)) == True
