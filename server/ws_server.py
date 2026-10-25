import asyncio
import websockets
import json
import os
import uuid
import time
import base64
from core.ticket import Ticket
from core.utils import print_separator
from modules.queue_manager import QueueManager
from loguru import logger
import ssl
import pathlib

class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=3060):
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.queue_manager = QueueManager()
        self.queue_manager.run_app_in_thread()
        self.ticket_ws_map = {}  
        
    async def handler(self, websocket):
        client_info = websocket.remote_address
        ip, puerto = client_info[0], client_info[1]
        client_str = f"{ip}:{puerto}"
        logger.info(f"🟢 Cliente conectado desde IP: {ip}, Puerto: {puerto}")
        self.connected_clients.add(websocket)
        try:
            while True:
                message = await websocket.recv()
                error = self._validate_message(message)
                if error:
                    await websocket.send(error)
                    continue
                try:
                    data = json.loads(message)
                except Exception:
                    await websocket.send("⚠️ Error al decodificar JSON.")
                    continue
                error = self._validate_data(data)
                if error:
                    await websocket.send(error)
                    continue
                # Permitir que el cliente envíe un id opcional
                client_id = data.get("id")
                pdf_path = None
                pdf_data = data.get("PDF", {}).get("data", None)
                # logger.debug(pdf_data)
                metadata = data["metadata"]
                if pdf_data:
                    # Permitir lista de bytes o base64
                    if isinstance(pdf_data, str):
                        try:
                            pdf_bytes = base64.b64decode(pdf_data)
                        except Exception:
                            await websocket.send("⚠️ PDF.data no es base64 válido.")
                            continue
                    elif isinstance(pdf_data, list):
                        try:
                            pdf_bytes = bytes(pdf_data)
                        except Exception:
                            await websocket.send("⚠️ PDF.data no es una lista de bytes válida.")
                            continue
                    else:
                        await websocket.send("⚠️ PDF.data debe ser base64 (string) o lista de bytes.")
                        continue
                    pdf_path = self._save_pdf_file(pdf_bytes, metadata.get("fileName", "documento.pdf"))
                    if isinstance(pdf_path, str) and pdf_path.startswith("⚠️"):
                        await websocket.send(pdf_path)
                        continue
                ticket = Ticket(
                    number=metadata["phoneNumber"],
                    message=metadata.get("message", ""),
                    client_info=client_str,
                    pdf_path=pdf_path,
                    ws=websocket,
                    id=client_id
                )
                # Guardar mapping ticket.id -> ws
                self.ticket_ws_map[ticket.id] = websocket
                # Calcular posición en la cola
                position = self.queue_manager.process_queue.qsize() + 1
                await websocket.send(f"🟢 Ticket encolado (ID: {ticket.id}). Hay {position-1} ticket(s) antes que el tuyo.")
                logger.info(f"📩 Ticket recibido:\n{ticket}")
                self.queue_manager.process_queue.put(ticket)
                logger.info(f"📥 Ticket encolado para 📲 {ticket.number}")
        except websockets.ConnectionClosed:
            logger.info(f"🔴 Cliente {client_str} desconectado.")
        finally:
            self.connected_clients.remove(websocket)

    def _validate_message(self, message):
        if not message:
            return "⚠️ Mensaje vacío."
        if len(message) > 10000000:  # 10 MB
            return "⚠️ Mensaje demasiado grande."
        if message.startswith("ping"):
            return "pong"
        if not message.startswith("{") or not message.endswith("}"):
            return "⚠️ Mensaje no es un JSON válido."
        return None

    def _validate_data(self, data):
        if not isinstance(data, dict):
            return "⚠️ El mensaje debe ser un objeto JSON."
        metadata = data.get("metadata")
        if not metadata:
            return "⚠️ No hay metadatos en el JSON."
        if not isinstance(metadata, dict):
            return "⚠️ 'metadata' debe ser un objeto."
        if "phoneNumber" not in metadata or not isinstance(metadata["phoneNumber"], str):
            return "⚠️ 'phoneNumber' es obligatorio y debe ser string."
        if "message" not in metadata or not isinstance(metadata["message"], str):
            return "⚠️ 'message' es obligatorio y debe ser string."
        if "fileName" in metadata and not isinstance(metadata["fileName"], str):
            return "⚠️ 'fileName' debe ser string si está presente."
        pdf = data.get("PDF")
        if pdf and not isinstance(pdf, dict):
            return "⚠️ 'PDF' debe ser un objeto si está presente."
        # Permitir base64 o lista de bytes
        if pdf and "data" in pdf and not (isinstance(pdf["data"], list) or isinstance(pdf["data"], str)):
            return "⚠️ 'PDF.data' debe ser una lista de bytes o un string base64."
        return None

    def _save_pdf_file(self, pdf_bytes, file_name):
        try:
            timestamp = int(time.time() * 1000)
            base_name = file_name.split(".")[0]
            ext = ".pdf"
            safe_name = f"{base_name}_{timestamp}{ext}"
            with open(safe_name, "wb") as pdf_file:
                pdf_file.write(pdf_bytes)
            logger.info(f"📄 PDF guardado como {safe_name} ({len(pdf_bytes)} bytes)")
            return os.path.abspath(safe_name)
        except Exception as e:
            return f"⚠️ Error al guardar el PDF: {e}"

    async def start(self):
        # Pasar el callback de notificación a la cola
        self.queue_manager.set_notify_callback(self.notify_ticket_status)

        # Crear contexto SSL
        # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # base_path = pathlib.Path(__file__).parent.resolve()
        # ssl_context.load_cert_chain(
        #     certfile=str(base_path / "owotech.crt"),
        #     keyfile=str(base_path / "owotech.key")
        # )

        # Iniciar servidor con SSL (wss://)
        async with websockets.serve(
            self.handler,
            self.host,
            self.port,
            max_size=None
            # ssl=ssl_context
        ):
            logger.info(f"🟢 Servidor WebSocket escuchando en ws://{self.host}:{self.port}")
            await asyncio.Future()

    async def notify_ticket_status(self, ticket, status, position=None):
        ws = ticket.ws or self.ticket_ws_map.get(ticket.id)
        if ws:
            try:
                if status == "processing":
                    await ws.send(f"🟡 Tu ticket (ID: {ticket.id}) está siendo procesado.")
                elif status == "done":
                    await ws.send(f"✅ Tu ticket (ID: {ticket.id}) ha sido procesado y enviado.")
                elif status == "queued":
                    await ws.send(f"🟢 Ticket encolado (ID: {ticket.id}). Hay {position} ticket(s) antes que el tuyo.")
            except Exception:
                pass

# Punto de entrada para main.py
async def main():
    logger.debug("Iniciando servidor WebSocket...")
    server = WebSocketServer()
    await server.start() 