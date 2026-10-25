import unittest
import asyncio
import os
from socket_manager import WebSocketProcessor
from unittest.mock import AsyncMock, patch, MagicMock
import json

class TestWebSocketProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = WebSocketProcessor()
    
    def test_get_available_browser(self):
        browser = self.processor.get_available_browser()
        self.assertIsNotNone(browser)
        self.assertEqual(browser, "chrome")
        self.processor.browser_status["chrome"] = True
        browser = self.processor.get_available_browser()
        self.assertIsNone(browser)
        self.processor.browser_status["chrome"] = False

    def test_process_task(self):
        web_manager_mock = MagicMock()
        task = {"number": "12345", "pdf_path": "test.pdf"}
        with patch("os.remove", MagicMock()) as remove_mock:
            with patch("builtins.print"):
                self.processor.process_task(web_manager_mock, task, "chrome")
            web_manager_mock.execute.assert_called_once_with(
                number="12345",
                message="Hola, este es un mensaje de prueba automatizado.",
                pdf_path="test.pdf"
            )
            remove_mock.assert_called_once_with("test.pdf")
            self.assertFalse(self.processor.browser_status["chrome"])
    

    def test_process_task_with_exception(self):
        web_manager_mock = MagicMock()
        web_manager_mock.execute.side_effect = Exception("Simulated Error")
        task = {"number": "12345", "pdf_path": "test.pdf"}
        with patch("os.remove", MagicMock()) as remove_mock:
            with patch("builtins.print") as mock_print: self.processor.process_task(web_manager_mock, task, "chrome")
            web_manager_mock.execute.assert_called_once_with(
                number="12345",
                message="Hola, este es un mensaje de prueba automatizado.",
                pdf_path="test.pdf"
            )
            remove_mock.assert_called_once_with("test.pdf")
            self.assertFalse(self.processor.browser_status["chrome"])
            mock_print.assert_any_call("[chrome] ⚠️ Error al procesar {'number': '12345', 'pdf_path': 'test.pdf'}: Simulated Error")

    def test_run_app_in_thread(self):
        with patch.object(self.processor, 'app', return_value=None):
            self.processor.run_app_in_thread()
            self.assertTrue(self.processor.process_queue.empty())

    @patch("websockets.connect")
    def test_start_listen(self, mock_websocket):
        """Prueba que el WebSocket recibe diferentes mensajes y los procesa correctamente"""
        mensajes = [
            json.dumps({
                "metadata": {"fileName": "test.pdf", "phoneNumber": "573027032694"},
                "PDF": {"data": [1, 2, 3, 4]}
                }),
            json.dumps({}),
            "{malformed_json",
            json.dumps({"PDF": {"data": [1, 2, 3, 4]}}),
            json.dumps({"metadata": {"fileName": "test.pdf", "phoneNumber": "573027032694"}}),
            RuntimeError("Error de conexión")
        ]
        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=mensajes + [asyncio.CancelledError()]) 
        mock_websocket.return_value.__aenter__.return_value = mock_ws
        processor = WebSocketProcessor()
        try: asyncio.run(processor.start_listen())
        except asyncio.CancelledError: pass  
        self.assertFalse(processor.process_queue.empty(), "La cola debería contener al menos una tarea válida")
        task = processor.process_queue.get()
        self.assertEqual(task["number"], "573027032694")
        self.assertTrue(task["pdf_path"].endswith("test.pdf"))
        self.assertGreater(mock_websocket.call_count, 1, "Se esperaba al menos un intento de reconexión")

    @patch('time.sleep', return_value=None)
    def test_app_queue_empty(self, mock_sleep):
        instance = MagicMock()
        instance.process_queue.empty.return_value = True
        stop_event = MagicMock()
        stop_event.is_set.side_effect = [False, True] 
        instance.app(stop_event=stop_event)
        instance.get_available_browser.assert_not_called()
        instance.process_queue.get.assert_not_called()

    def tearDown(self):
        """Elimina test.pdf después de cada prueba si existe."""
        if os.path.exists("test.pdf"):
            os.remove("test.pdf")
