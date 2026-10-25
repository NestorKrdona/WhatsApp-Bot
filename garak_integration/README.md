# Arnes de pruebas del Punto 3 (equipo purpura) — Garak + WhatsApp-Bot

Este directorio contiene el codigo que conecta **Garak** (https://garak.ai/), la
herramienta elegida como motor de equipo rojo para el Punto 3, con el canal real
de WhatsApp de pruebas, a traves de **WhatsApp-Bot** (este mismo repositorio),
adaptado unicamente como interfaz de entrega y captura de mensajes.

No reemplaza el documento "Borrador - Puntos 2, 3 y 4.docx": los scripts de aqui
generan la evidencia (transcripciones, resultados) que luego se pega en los campos
"Configuracion utilizada / Registros y capturas / Resultado obtenido / Hallazgos"
de cada caso de prueba en ese documento.

## Por que Garak

Garak esta construido especificamente para red-teaming automatizado de LLMs: genera
sondas de ataques conocidos (prompt injection, jailbreak, fuga de system prompt) y
las evalua con detectores ya existentes, en lugar de tener que construir ese cata-
logo de ataques desde cero como habria que hacer con Giskard o Evidently AI (mas
orientados a calidad/robustez de modelos y a monitoreo de drift, respectivamente).

Garak no sabe hablar WhatsApp de forma nativa (sus generators estandar llaman APIs
de modelos como OpenAI). Por eso se construyo `whatsapp_generator.py`: un generator
personalizado que entrega cada sonda al canal de WhatsApp de pruebas y devuelve la
respuesta real del agente como si fuera la salida directa del modelo.

## Que se ajusto en el WhatsApp-Bot

El bot (`modules/web_manager.py`, `modules/queue_manager.py`, `server/ws_server.py`,
`core/ticket.py`) originalmente solo *enviaba* mensajes; no leia ni devolvia la
respuesta del otro lado de la conversacion. Se le agrego, de forma retrocompatible
(el comportamiento normal de notificaciones de produccion no cambia):

- Un campo opcional `captureReply` en el JSON que el cliente WebSocket envia.
- `BaseWebHandler.wait_for_reply()` / `get_last_incoming_message()` en
  `web_manager.py`, que esperan a que aparezca un nuevo mensaje entrante en el chat
  abierto y devuelven su texto.
- Cuando `captureReply=true`, el servidor WebSocket envia, ademas de la notificacion
  humana habitual, un mensaje JSON `{"ticketId", "status": "done", "reply": "..."}`
  con el texto capturado.

Estos selectores (`div.message-in`, `span.selectable-text`) dependen de la version
actual del DOM de WhatsApp Web; si WhatsApp cambia su interfaz, hay que revisarlos
y ajustarlos (abrir WhatsApp Web, inspeccionar un mensaje entrante con las
herramientas de desarrollador del navegador, y actualizar los selectores en
`web_manager.py`).

## Requisitos

- El WhatsApp-Bot corriendo normalmente (`python main.py`), con una sesion de
  WhatsApp Web **ya autenticada** (QR escaneado) en el **numero de pruebas**, nunca
  en el numero oficial de soporte.
- `pip install garak` (no se agrego a `requirements.txt` del bot para no mezclar
  dependencias de pruebas con las de produccion; instalarlo aparte o en un entorno
  virtual de pruebas).
- `websocket-client` ya esta en `requirements.txt` del proyecto.

## Variables de entorno comunes

| Variable                  | Uso                                                              |
|----------------------------|-------------------------------------------------------------------|
| `WHATSAPP_BOT_WS_URL`      | URL del servidor del bot (por defecto `ws://localhost:3060`)     |
| `WHATSAPP_TEST_NUMBER`     | Numero de pruebas (usado por el generator de Garak)              |
| `WHATSAPP_REPLY_TIMEOUT`   | Segundos a esperar la respuesta del agente (por defecto 90)      |

## Como ejecutar

**Caso de prueba 1 (validacion de identidad y suplantacion)** — logica propia de la
aplicacion, no cubierta por las sondas estandar de Garak:

```bash
export CASE1_UNREGISTERED_NUMBER="<numero no registrado>"
export CASE1_STUDENT_ID="<numero de identificacion del estudiante de prueba 'Estudiante'>"
python garak_integration/run_case1_identidad.py
```

**Caso de prueba 2 (inyeccion de prompt directa)** — version con las sondas curadas
que ya describe el documento del Punto 3:

```bash
export CASE2_STUDENT_NUMBER="<numero de pruebas 'Estudiante', ya autenticado>"
export CASE2_OTHER_STUDENT_ID="<numero de identificacion de otro estudiante ficticio>"
python garak_integration/run_case2_injection.py
```

**Caso de prueba 2, cobertura ampliada con Garak** (opcional, requiere Garak
instalado):

```bash
PYTHONPATH=. WHATSAPP_TEST_NUMBER="<numero de pruebas 'Estudiante'>" python -m garak \
    --model_type garak_integration.whatsapp_generator.WhatsAppGenerator \
    --probes promptinject,dan.DAN_Jailbreak,leakreplay
```

Verificar los nombres de probes disponibles en la version instalada con
`python -m garak --list_probes`, porque cambian entre versiones de Garak.

## Salida

Los dos scripts `run_case*.py` escriben en `garak_integration/results/` un `.json`
(datos crudos) y un `.md` (resumen legible, con una checklist de revision manual
frente a los criterios de aceptacion de ese caso). Ese `.md` es lo que se pega en
el documento del Punto 3. La ejecucion de Garak por CLI escribe su propio reporte
(HTML/JSONL) segun la configuracion de Garak; referenciarlo igualmente como
evidencia de ejecucion.

## Limitaciones a tener en cuenta (ya reflejadas en el Punto 3 del documento)

- Esto ejecuta contra un **numero de pruebas**, no contra el canal oficial operado
  por Vox Ally / API de Meta Business: no valida comportamientos propios de esa capa
  de transporte (limites de tasa, verificacion de numero, etc.).
- Requiere una sesion de WhatsApp Web autenticada y visible para el navegador del
  bot; no es apto para correrse desatendido sin esa sesion activa.
- Los selectores de captura de respuesta son fragiles frente a cambios de WhatsApp
  Web; revisar si `reply` vuelve `None` de forma sistematica.
