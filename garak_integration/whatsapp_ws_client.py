"""
Cliente sincrono minimo para el servidor WebSocket del WhatsApp-Bot (server/ws_server.py),
pensado para el arnes de pruebas del Punto 3 (equipo purpura). Envia un ticket con
captureReply=true y bloquea hasta recibir el mensaje JSON de respuesta ("status": "done")
que el servidor envia una vez el bot captura la respuesta real del agente en WhatsApp Web
(ver modules/web_manager.py: BaseWebHandler.wait_for_reply / BaseWebHandler.execute).

No requiere Garak: se puede usar de forma independiente (ver run_case1_identidad.py).
"""
import json
import time
import uuid
import websocket  # paquete websocket-client, ya listado en requirements.txt


class WhatsAppTestClient:
    def __init__(self, url="ws://localhost:3060", connect_timeout=10):
        self.url = url
        self.connect_timeout = connect_timeout

    def send_and_wait_reply(self, phone_number, message, timeout=90):
        """Envia un mensaje de prueba al numero indicado y espera la respuesta real
        del agente, capturada por el bot. Devuelve (reply_text_o_None, eventos_crudos)."""
        ticket_id = str(uuid.uuid4())
        payload = {
            "id": ticket_id,
            "metadata": {
                "phoneNumber": phone_number,
                "message": message,
                "captureReply": True,
            },
        }

        ws = websocket.create_connection(self.url, timeout=self.connect_timeout)
        events = []
        reply = None
        try:
            ws.send(json.dumps(payload, ensure_ascii=False))
            deadline = time.time() + timeout
            while time.time() < deadline:
                ws.settimeout(max(1, deadline - time.time()))
                try:
                    raw = ws.recv()
                except Exception:
                    break
                events.append(raw)
                try:
                    data = json.loads(raw)
                except (TypeError, ValueError):
                    continue
                if isinstance(data, dict) and data.get("ticketId") == ticket_id and data.get("status") == "done":
                    reply = data.get("reply")
                    break
        finally:
            try:
                ws.close()
            except Exception:
                pass

        return reply, events
