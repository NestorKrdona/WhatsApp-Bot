import os
import pytest
from datetime import datetime

from src.modules.db_manager import CSVHandler

@pytest.fixture
def setup_csv():
    """Fixture para crear un archivo CSV temporal para las pruebas."""
    handler = CSVHandler("test")
    yield handler 
    handler.delete()

def test_insert(setup_csv):
    """Inserta datos y verifique la cantidad e informacion insertada"""
    handler = setup_csv
    data = [str(datetime.now().date()), 'type1', 'data1']
    handler.insert(data)
    rows = handler.read_all()
    assert len(rows) == 1
    assert rows[0] == data

def test_read_all(setup_csv):
    """Inserta 2 datos y verifica que obtiene las 2 y corresponde a lo insertado"""
    handler = setup_csv
    data1 = [str(datetime.now().date()), 'type1', 'data1']
    data2 = [str(datetime.now().date()), 'type2', 'data2']
    handler.insert(data1)
    handler.insert(data2)
    rows = handler.read_all()
    assert len(rows) == 2
    assert rows[0] == data1
    assert rows[1] == data2

def test_clear(setup_csv):
    """Inserta datos y despues comprueba que se eliminaron"""
    handler = setup_csv
    data = [str(datetime.now().date()), 'type1', 'data1']
    handler.insert(data)
    handler.clear()
    rows = handler.read_all()
    assert len(rows) == 0

def test_get_by_date(setup_csv):
    """Inserta varias datos con fechas diferentes e iguales y obtiene la cantidad filtrada por fecha"""
    handler = setup_csv
    date1 = str(datetime.now().date())
    date2 = '2025-02-01'
    data1 = [date1, 'type1', 'data1']
    data2 = [date2, 'type2', 'data2']
    data3 = [date1, 'type3', 'data3']
    handler.insert(data1)
    handler.insert(data2)
    handler.insert(data3)
    result = handler.get_by_date(date1)
    assert len(result) == 2
    assert result[0] == data1
    assert result[1] == data3

def test_delete(setup_csv):
    """Se compueba el estado del documento si esta creado y si se elimina correctamente"""
    handler = setup_csv
    test_file = handler.file_name
    assert os.path.exists(test_file)
    
    handler.delete()
    assert not os.path.exists(test_file)
