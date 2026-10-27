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

## Remitente vs. destino (importante)

El bot no tiene un numero propio "registrado" en ningun archivo: el REMITENTE de
cada mensaje es, literalmente, la cuenta de WhatsApp cuyo codigo QR se escaneo en
la sesion de WhatsApp Web que controla el bot. El campo `phoneNumber` que viaja en
cada ticket (y las variables `AGENT_TEST_NUMBER` / `WHATSAPP_AGENT_NUMBER` de abajo)
es el DESTINO: el numero del canal de pruebas del agente, al que se le escribe.

Esto implica que, como solo hay una sesion de WhatsApp Web autenticada a la vez:

- Para correr el **Caso de prueba 1**, el QR debe escanearse con el telefono del
  numero NO registrado (`CASE1_UNREGISTERED_NUMBER`).
- Para correr el **Caso de prueba 2**, el QR debe escanearse con el telefono del
  numero de pruebas "Estudiante" (`CASE2_STUDENT_NUMBER`).
- Para pasar de un caso al otro hay que cerrar sesion en WhatsApp Web (o borrar la
  carpeta de perfil en `modules/browser_profiles/`) y volver a escanear con el otro
  telefono.

## Variables de entorno comunes

| Variable                  | Uso                                                                 |
|----------------------------|----------------------------------------------------------------------|
| `WHATSAPP_BOT_WS_URL`      | URL del servidor del bot (por defecto `ws://localhost:3060`)        |
| `AGENT_TEST_NUMBER`        | Numero de WhatsApp del canal de pruebas del agente (DESTINO), usado por `run_case1_identidad.py` y `run_case2_injection.py` |
| `WHATSAPP_AGENT_NUMBER`    | Igual que `AGENT_TEST_NUMBER`, pero para el generator de Garak (`whatsapp_generator.py`) |
| `WHATSAPP_TEST_NUMBER`     | Numero de pruebas autenticado (identidad del REMITENTE, solo como etiqueta/arg de Garak) |
| `WHATSAPP_REPLY_TIMEOUT`   | Segundos a esperar la respuesta del agente (por defecto 90)         |

## Como ejecutar

**Caso de prueba 1 (validacion de identidad y suplantacion)** — logica propia de la
aplicacion, no cubierta por las sondas estandar de Garak:

```bash
export AGENT_TEST_NUMBER="<numero de WhatsApp del canal de pruebas del agente>"
export CASE1_UNREGISTERED_NUMBER="<numero no registrado>"
export CASE1_STUDENT_ID="<numero de identificacion del estudiante de prueba 'Estudiante'>"
python garak_integration/run_case1_identidad.py
```

**IMPORTANTE — cual de los dos scripts de abajo usa Garak de verdad:**
`run_case2_injection.py` NO importa ni ejecuta Garak: es un script propio con 3
mensajes curados a mano, pensado como complemento rapido o respaldo si Garak no esta
instalado. El que si importa y corre el motor real de Garak (sus probes, sus
detectores, su reporte oficial) es `run_case2_garak.py`. Para que el Punto 3 refleje
honestamente el uso de Garak que describe, el que hay que correr (ademas o en lugar
del anterior) es este segundo.

**Caso de prueba 2, version propia (sondas curadas a mano, SIN Garak)**:

```bash
export AGENT_TEST_NUMBER="<numero de WhatsApp del canal de pruebas del agente>"
export CASE2_STUDENT_NUMBER="<numero de pruebas 'Estudiante', ya autenticado>"
export CASE2_OTHER_STUDENT_ID="<numero de identificacion de otro estudiante ficticio>"
python garak_integration/run_case2_injection.py
```

**Caso de prueba 2, con Garak real** (requiere `pip install garak`; recomendado,
este es el que corresponde a la herramienta que justifica el Punto 3):

```bash
export AGENT_TEST_NUMBER="<numero de WhatsApp del canal de pruebas del agente>"
export WHATSAPP_TEST_NUMBER="<numero de pruebas 'Estudiante', ya autenticado>"
python garak_integration/run_case2_garak.py
```

Este wrapper arma y corre internamente:

```bash
PYTHONPATH=. python -m garak \
    --model_type whatsapp_generator.WhatsAppGenerator \
    --model_name "$WHATSAPP_TEST_NUMBER" \
    --probes promptinject.HijackHateHumans,dan.DAN_Jailbreak,leakreplay.GuardianCloze
```

Antes de correr Garak, el script copia automaticamente `whatsapp_generator.py`
dentro de `garak/generators/` del propio paquete instalado en tu entorno virtual
(`venv/lib/.../site-packages/garak/generators/whatsapp_generator.py`). Esto es
necesario porque el cargador de plugins de Garak 0.17.1 solo importa generators como
submodulos de `garak.generators.*`; no soporta un modulo externo via `PYTHONPATH`
como se penso originalmente. La copia se sobre-escribe en cada corrida, asi que
siempre queda sincronizada con el codigo de este repositorio: no hay que tocar nada
manualmente dentro de la instalacion de Garak.

y copia el/los reporte(s) oficiales de Garak (`.report.jsonl` y `.report.html`,
generados por Garak en `~/.local/share/garak/garak_runs/`) a `garak_integration/results/`.

El script separa las sondas en dos grupos y, si hay sondas en ambos, hace DOS
invocaciones de `python -m garak` (cada una con su propio `run_uuid` y su propio
reporte), porque `--generations` es un parametro global de la corrida y no se puede
fijar distinto por sonda en una sola invocacion:

- **Sondas escaladas** (`GARAK_SCALED_PROBES`, por defecto solo
  `promptinject.HijackHateHumans`): autoescalan su cantidad de prompts, asi que se
  limitan con `GARAK_PROMPT_CAP` (por defecto 30; el valor por defecto de Garak es
  256, que fue lo que produjo los 256 prompts y las ~3 horas de la primera corrida
  — internamente esto se pasa como `run.soft_probe_prompt_cap` en un archivo de
  configuracion temporal, porque esta version de Garak no tiene un flag de linea de
  comandos para ese valor) y se corren siempre con `generations=1`, para que el
  total de intentos sea exactamente el cap (30 intentos, no 30 x generations).
- **Sondas de conteo fijo** (todas las que no estan en `GARAK_SCALED_PROBES`, por
  defecto `dan.DAN_Jailbreak` y `leakreplay.GuardianCloze`): no autoescalan, asi que
  `GARAK_PROMPT_CAP` no las afecta; para obtener mas muestras se repiten con
  `GARAK_GENERATIONS` (por defecto 3) contra el canal real.

Tambien se puede cambiar la lista completa de sondas con `GARAK_PROBES` (lista
separada por comas). Verificar los nombres de probes disponibles en la version
instalada con
`python -m garak --list_probes`, porque cambian entre versiones de Garak.

Nota sobre version de Garak: el generator (`whatsapp_generator.py`) usa las clases
`Message`/`Conversation` de la API actual de Garak para leer el prompt y devolver la
respuesta; si la version instalada es mas antigua y usa strings planos, el generator
detecta esto automaticamente y cae de nuevo a ese modo (ver comentarios en el codigo).

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
