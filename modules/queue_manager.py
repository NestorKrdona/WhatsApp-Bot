import threading
import queue
import time
import os
import traceback
from modules.web_manager import WebHandler
from core.ticket import Ticket
import asyncio
from loguru import logger

class QueueManager:
    def __init__(self):
        self.browser_status = {browser: False for browser in ["chrome"]}
        self.browser_lock = threading.Lock()
        self.process_queue = queue.Queue()
        self.notify_callback = None
        self.main_loop = None

    def set_notify_callback(self, callback):
        self.notify_callback = callback
        # Guardar el loop principal de asyncio
        try:
            self.main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.main_loop = None

    @staticmethod
    def _unpack_result(result):
        """Normaliza el valor de retorno de WebHandler.execute(): puede ser un bool
        (comportamiento original) o un dict {"success", "reply"} cuando el ticket
        pidio captura de respuesta para el arnes de pruebas del Punto 3."""
        if isinstance(result, dict):
            return result.get("success", False), result.get("reply")
        return bool(result), None

    def process_ticket(self, ticket, browser):
        logger.info(f"🔍 Procesando ticket 📲 {ticket.number} con {browser}")
        web_manager = WebHandler(browser=browser)
        with self.browser_lock: self.browser_status[browser] = True
        # Notificar al cliente que su ticket está siendo procesado
        if self.notify_callback and self.main_loop:
            try:
                asyncio.run_coroutine_threadsafe(self.notify_callback(ticket, "processing"), self.main_loop)
            except Exception:
                pass
        logger.info(f"🟡 [{browser}] Procesando ticket 📲 {ticket.number}")
        
        reply_text = None
        try:
            result = web_manager.execute(
                message=ticket.message,
                number=ticket.number,
                pdf_path=ticket.pdf_path,
                test=ticket.test,
                capture_reply=ticket.capture_reply
            )
            success, reply_text = self._unpack_result(result)
            if not success:
                web_manager.driver.quit()
                logger.info(f"🔄 [{browser}] Reintentando ticket 📲 {ticket.number}")
                web_manager = WebHandler(browser=browser)
                result = web_manager.execute(
                    message=ticket.message,
                    number=ticket.number,
                    pdf_path=ticket.pdf_path,
                    test=ticket.test,
                    capture_reply=ticket.capture_reply
                )
                success, reply_text = self._unpack_result(result)
        except Exception as e:
            logger.error(f"❌ [{browser}] Error al procesar ticket 📲 {ticket.number}: {e}")
            traceback.print_exc()
        logger.info(f"✅ [{browser}] Ticket 📲 {ticket.number} finalizado")
        # Notificar al cliente que su ticket fue procesado
        if self.notify_callback and self.main_loop:
            try:
                asyncio.run_coroutine_threadsafe(self.notify_callback(ticket, "done", reply=reply_text), self.main_loop)
            except Exception:
                pass
        if ticket.pdf_path and os.path.exists(ticket.pdf_path):
            os.remove(ticket.pdf_path)
        with self.browser_lock: self.browser_status[browser] = False

    def get_available_browser(self):
        with self.browser_lock:
            for browser, status in self.browser_status.items():
                if not status: return browser
        return None

    def app(self, stop_event=None):
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            while stop_event is None or not stop_event.is_set():
                if self.process_queue.empty():
                    time.sleep(2)
                    continue
                browser = self.get_available_browser()
                if browser:
                    ticket = self.process_queue.get()
                    logger.info(f"🚀 Asignando ticket 📲 {ticket.number} a {browser}")
                    executor.submit(self.process_ticket, ticket, browser)
                else:
                    time.sleep(1)

    def run_app_in_thread(self):
        thread = threading.Thread(target=self.app, daemon=True)
        thread.start() 