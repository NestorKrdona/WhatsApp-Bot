# WhatsApp Bot - Sistema de Mensajería Automática

## 🚀 Características Principales

- **Envío automático de mensajes** a números de WhatsApp
- **Soporte para archivos PDF** adjuntos
- **Múltiples navegadores** (Chrome, Firefox, Edge, Opera, Chromium)
- **Sistema de colas** para procesar múltiples tickets
- **Servidor WebSocket** para comunicación en tiempo real
- **Logging avanzado** con rotación diaria de archivos
- **Autenticación automática con código QR** cuando la sesión expira

## 📋 Requisitos

- Python 3.8+
- Navegador web (Chrome, Firefox, Edge, Opera, Chromium)
- Conexión a internet

## 🛠️ Instalación

1. **Clonar el repositorio:**
```bash
git clone <url-del-repositorio>
cd Whatsapp
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar API Key (opcional):**
   - Ve a [https://api.imgbb.com/](https://api.imgbb.com/)
   - Regístrate y obtén tu API key gratuita
   - Edita `config/api_keys.py`:
   ```python
   IMGBB_API_KEY = "tu_api_key_aqui"
   ```

## 🚀 Uso

### Iniciar el servidor

```bash
python main.py
```

El servidor WebSocket se iniciará en `ws://localhost:3060`

### Enviar mensaje desde Python

```python
from modules.web_manager import WebHandler

# Crear instancia
web_handler = WebHandler(browser="chrome")

# Enviar mensaje
data = {
    "number": "3027032694",
    "message": "Hola desde el bot!",
    "pdf_path": "documento.pdf",  # Opcional
    "test": False
}

web_handler.execute(**data)
```

### Enviar mensaje vía WebSocket

```python
import asyncio
import websockets
import json

async def send_message():
    uri = "ws://localhost:3060"
    async with websockets.connect(uri) as websocket:
        message = {
            "metadata": {
                "phoneNumber": "3027032694",
                "message": "Hola desde WebSocket!"
            }
        }
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        print(f"Respuesta: {response}")

asyncio.run(send_message())
```

## 🔧 Configuración

### Logging

El sistema incluye logging avanzado con loguru:

- **Rotación diaria** de archivos de log
- **Retención configurable** (30 días para logs normales, 90 días para errores)
- **Compresión automática** de archivos antiguos
- **Múltiples niveles** de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Los logs se guardan en la carpeta `logs/`:
```
logs/
├── whatsapp_bot_2024-01-15.log    # Logs completos del día
├── errors_2024-01-15.log          # Solo errores del día
└── whatsapp_bot_2024-01-14.log.zip  # Archivos comprimidos
```

### Autenticación con Código QR

Cuando WhatsApp Web requiere autenticación:

1. **Detección automática** del código QR
2. **Captura de imagen** del canvas del QR
3. **Subida a la nube** (ImgBB o servicio alternativo)
4. **URL temporal** para escanear desde el teléfono
5. **Espera automática** hasta completar la autenticación
6. **Limpieza** de archivos temporales

## 📁 Estructura del Proyecto

```
Whatsapp/
├── core/
│   ├── logger_config.py      # Configuración de logging
│   ├── qr_handler.py         # Manejo de código QR
│   ├── ticket.py             # Modelo de ticket
│   └── utils.py              # Utilidades
├── modules/
│   ├── web_manager.py        # Manejo de navegadores
│   └── queue_manager.py      # Sistema de colas
├── server/
│   └── ws_server.py          # Servidor WebSocket
├── config/
│   └── api_keys.py           # Configuración de API keys
├── docs/
│   ├── LOGGING.md            # Documentación de logging
│   └── QR_AUTHENTICATION.md  # Documentación de autenticación QR
├── logs/                     # Archivos de log (auto-creado)
├── temp/                     # Archivos temporales (auto-creado)
├── main.py                   # Punto de entrada
├── socket_client.py          # Cliente de prueba
├── test_logging.py           # Pruebas de logging
├── test_qr_handler.py        # Pruebas de código QR
└── requirements.txt          # Dependencias
```

## 🧪 Pruebas

### Probar sistema de logging

```bash
python test_logging.py
```

### Probar autenticación QR

```bash
python test_qr_handler.py
```

### Probar cliente WebSocket

```bash
python socket_client.py
```

## 📖 Documentación

- [Sistema de Logging](docs/LOGGING.md)
- [Autenticación con Código QR](docs/QR_AUTHENTICATION.md)

## 🔍 Solución de Problemas

### Error: "No se pudo iniciar Chrome"
- Verifica que Chrome esté instalado
- El sistema intentará rutas alternativas automáticamente

### Error: "Sesión de WhatsApp Web cerrada"
- El sistema detectará automáticamente y mostrará el código QR
- Escanea el código desde tu teléfono

### Error: "API Key no configurada"
- Configura la API key de ImgBB o el sistema usará servicios alternativos
- No es crítico para el funcionamiento básico

### Error: "Timeout esperando escaneo"
- Verifica la URL del código QR en los logs
- Asegúrate de escanear desde WhatsApp en tu teléfono

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ⚠️ Disclaimer

Este bot es para uso educativo y de desarrollo. Asegúrate de cumplir con los términos de servicio de WhatsApp y las leyes locales de tu jurisdicción.

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs en la carpeta `logs/`
2. Consulta la documentación en `docs/`
3. Ejecuta los scripts de prueba
4. Verifica la configuración de API keys

---

**¡Disfruta usando el WhatsApp Bot! 🚀** 