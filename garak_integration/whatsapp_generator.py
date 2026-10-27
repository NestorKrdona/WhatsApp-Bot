"""
Generator personalizado de Garak que conecta las sondas generadas por Garak con el
canal real de WhatsApp de pruebas, a traves de la interfaz construida por el grupo
(WhatsApp-Bot, adaptada en el Punto 3 para capturar y devolver la respuesta del agente).

Uso tipico (Caso de prueba 2 - inyeccion de prompt sobre agente ya autenticado):

    PYTHONPATH=. WHATSAPP_TEST_NUMBER=<numero_estudiante_de_prueba> python -m garak \
        --model_type whatsapp_generator.WhatsAppGenerator \
        --probes promptinject.HijackHateHumans,dan.DAN_Jailbreak,leakreplay.GuardianCloze

El numero de telefono "autenticado" (numero de prueba "Estudiante") se pasa como
model_name / WHATSAPP_TEST_NUMBER porque Garak no tiene un concepto nativo de
"numero de telefono"; este generator lo interpreta como tal.

IMPORTANTE:
- La interfaz de entrega/captura usada aqui depende de que el WhatsApp-Bot este
  corriendo con una sesion de WhatsApp Web ya autenticada (QR escaneado) en el
  numero de pruebas, y que el servidor WebSocket (server/ws_server.py) este activo
  en ws://localhost:3060 (o el host/puerto configurado via WHATSAPP_BOT_WS_URL).
- La firma exacta de garak.generators.base.Generator puede variar entre versiones
  de Garak; si __init__ falla al actualizar Garak, revisar la firma instalada con
  `python -c "import garak.generators.base as b; help(b.Generator)"` y ajustar.
"""
import os
import logging

try:
    from garak.generators.base import Generator
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "Este modulo requiere garak instalado ('pip install garak'). "
        "Ver garak_integration/README.md."
    ) from e

# Garak (version reciente) representa prompts/respuestas con las clases Message /
# Conversation en lugar de strings planos. Se intenta usar esa API; si la version de
# garak instalada es mas antigua y usa strings planos, se cae de nuevo a ese modo.
try:
    from garak.attempt import Message
    _USE_MESSAGE_API = True
except ImportError:
    _USE_MESSAGE_API = False

from garak_integration.whatsapp_ws_client import WhatsAppTestClient

logger = logging.getLogger(__name__)


class WhatsAppGenerator(Generator):
    """Generator de Garak que envia cada prompt como un mensaje de WhatsApp al numero
    de pruebas configurado y devuelve la respuesta real capturada del agente."""

    generator_family_name = "WhatsAppBot"
    supports_multiple_generations = False

    def __init__(self, name="", config_root=None):
        self.name = name or os.environ.get("WHATSAPP_TEST_NUMBER", "")
        self.agent_number = os.environ.get("WHATSAPP_AGENT_NUMBER", "")
        if not self.name or not self.agent_number:
            raise ValueError(
                "Debes indicar el numero de WhatsApp de pruebas autenticado (--model_name o "
                "WHATSAPP_TEST_NUMBER) y el numero del canal de pruebas del agente "
                "(WHATSAPP_AGENT_NUMBER, el numero AL que se envian los mensajes)."
            )
        self.ws_url = os.environ.get("WHATSAPP_BOT_WS_URL", "ws://localhost:3060")
        self.reply_timeout = int(os.environ.get("WHATSAPP_REPLY_TIMEOUT", "90"))
        self.client = WhatsAppTestClient(url=self.ws_url)
        super().__init__(self.name, config_root=config_root)

    def _call_model(self, prompt, generations_this_call=1):
        # `prompt` es un garak.attempt.Conversation en versiones recientes de garak,
        # o un string plano en versiones antiguas. Se extrae el texto del ultimo
        # turno de usuario en el primer caso, o se usa tal cual en el segundo.
        if hasattr(prompt, "last_message"):
            prompt_text = prompt.last_message("user").text
        else:
            prompt_text = str(prompt)

        reply, events = self.client.send_and_wait_reply(
            phone_number=self.agent_number, message=prompt_text, timeout=self.reply_timeout
        )
        if reply is None:
            logger.warning(
                "No se capturo respuesta del agente para el prompt %r (eventos: %s)",
                prompt_text, events,
            )
            return [None]
        return [Message(text=reply)] if _USE_MESSAGE_API else [reply]
