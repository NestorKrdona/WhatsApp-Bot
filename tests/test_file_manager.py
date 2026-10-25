import pytest
import os
import shutil
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.modules.reader_manager import ReaderHandler
from src.modules.db_manager import CSVHandler
from src.utils import get_yesterday_date, get_yesterday_month, get_local_path, get_cloud_path
from src.modules.file_manager import FileHandler  
from unittest import mock

@pytest.fixture
def mock_csv_handler():
    mock_handler = MagicMock(spec=CSVHandler)
    return mock_handler

@pytest.fixture
def mock_reader_handler():
    mock_reader = MagicMock(spec=ReaderHandler)
    mock_reader.excel_sum_column.return_value = 100 
    return mock_reader

@pytest.fixture
def file_handler(mock_csv_handler, mock_reader_handler):
    mock_csv_handler.insert.return_value = None
    handler = FileHandler("test")
    handler.db_manager = mock_csv_handler
    handler.reader_manager = mock_reader_handler
    yield handler
    CSVHandler("test").delete()

def test_path_no_creation(file_handler):
    base_dir = get_local_path(False, relative_to=2)
    with mock.patch("os.path.exists", return_value=True):
        with mock.patch("os.makedirs") as mock_makedirs:
            file_handler.init_folders(base_dir)
            mock_makedirs.assert_not_called()
            
def test_path_creation(file_handler):
    base_dir = get_local_path(False, relative_to=2)
    with mock.patch("os.path.exists", return_value=False):
        with mock.patch("os.makedirs") as mock_makedirs:
            file_handler.init_folders(base_dir)
            mock_makedirs.assert_any_call(f"{base_dir}\\{get_yesterday_month()}\\SISRED\\RETIROS\\LAFORTUNA")

@patch('os.makedirs') 
@patch('os.path.exists')  
def test_init_folders(mock_exists, mock_makedirs, file_handler):
    """Verifica que la estructura de carpetas se cree correctamente"""
    base_dir = get_local_path(True, relative_to=2)
    paths_to_check = [
        os.path.join(base_dir, "SIGA", "RECARGAS"),
        os.path.join(base_dir, "SIGA", "RETIROS"),
        os.path.join(base_dir, "SISRED", "RECARGAS", "LAFORTUNA"),
        os.path.join(base_dir, "SISRED", "RETIROS", "LAFORTUNA")
    ]
    mock_exists.return_value = False 
    for path in paths_to_check:
        mock_exists.return_value = False  
        if not os.path.exists(path):
            os.makedirs(path) 
            mock_exists.return_value = True
        assert os.path.exists(path)
    for path in paths_to_check:
        mock_makedirs.assert_any_call(path)
        mock_exists.assert_any_call(path)
    mock_exists.return_value = False

@patch('shutil.copy')
@patch('shutil.move')
def test_file_move(mock_move, mock_copy, file_handler):
    """Verifica que los archivos se muevan y copien correctamente"""
    file_name = "test.csv"
    file_handler.file_move(file_name, "RECARGAS", "SISRED", 4, 3, "LAFORTUNA")
    local_path = get_local_path(True) + f"\\SISRED\\RECARGAS\\LAFORTUNA\\{file_handler.date}.csv"
    cloud_path = get_cloud_path(True) + f"\\SISRED\\RECARGAS\\LAFORTUNA\\{file_handler.date}.csv"
    mock_move.assert_called_with(file_name, local_path)
    mock_copy.assert_called_with(file_name, cloud_path)
    file_handler.db_manager.insert.assert_called_once_with([file_handler.date, 'RECARGAS SISRED LAFORTUNA', 100])


def test_siga_organize(file_handler):
    with mock.patch("os.listdir", return_value=["Recargas.csv", "Pagos.txt"]):
        with mock.patch("os.path.isfile", return_value=True):
            with mock.patch.object(file_handler, "file_move") as mock_file_move:
                file_handler.siga_organize()
                expected_calls = [
                    mock.call(f"{get_local_path(True)}\\Recargas.csv", "RECARGAS", "SIGA", 0, 1, filter="ACTIVO"),
                    mock.call(f"{get_local_path(True)}\\Pagos.txt", "RETIROS", "SIGA", 0, 18)
                ]
                mock_file_move.assert_has_calls(expected_calls)

def test_sisred_organize(file_handler):
    with mock.patch("os.listdir", return_value=["RecaudosONL_document1.pdf", "RestirosXComerOnline.pdf"]):
        with mock.patch("os.path.isfile", return_value=True):
            with mock.patch.object(file_handler, "file_move") as mock_file_move:
                file_handler.sisred_organize()
                expected_calls = [
                    mock.call(f"{get_local_path(True)}\\RecaudosONL_document1.pdf", "RECARGAS", "SISRED", 4, 3, alias=None),
                    mock.call(f"{get_local_path(True)}\\RestirosXComerOnline.pdf", "RETIROS", "SISRED", 4, 3, alias=None)
                ]
                mock_file_move.assert_has_calls(expected_calls)