import json
import uuid
import re

class Ticket:
    @staticmethod
    def clean_bmp(texto):
        # Elimina caracteres fuera del BMP (U+0000 a U+FFFF)
        return re.sub(r'[\U00010000-\U0010FFFF]', '', texto)

    def __init__(self, number, message, client_info, pdf_path=None, ws=None, id=None, capture_reply=False):
        self.test = False
        if message.startswith("TEST"): 
            message = message.replace("TEST", "").strip()
            self.test = True
        message = self.clean_bmp(message)
        self.number = number
        self.message = message
        self.client_info = client_info
        self.pdf_path = pdf_path
        self.ws = ws
        self.id = id or str(uuid.uuid4())
        # Indica si el ticket proviene del arnes de pruebas del Punto 3 (Garak) y
        # requiere que se capture y se devuelva la respuesta del agente.
        self.capture_reply = capture_reply
        
    def __str__(self):
        pdf = f"📄 {self.pdf_path}" if self.pdf_path else ""
        separator = "-" * 50
        return (
            f"{separator}\n"
            f"🆔 Ticket ID: {self.id}\n"
            f"📲 Numero: {self.number}\n"
            f"👤 Cliente: {self.client_info}\n"
            f"💬 Mensaje: '{self.message}'\n"
            f"🧪 Prueba: {self.test}\n"
            f"🔁 Captura de respuesta (Garak): {self.capture_reply}\n"
            # f"{pdf}\n"
            f"{separator}"
        )