# Autenticación con Código QR de WhatsApp Web

## Descripción

El sistema ahora incluye funcionalidad automática para manejar la autenticación de WhatsApp Web cuando la sesión está cerrada. Cuando se detecta que se requiere escanear un código QR, el sistema:

1. **Captura automáticamente** el código QR de WhatsApp Web
2. **Sube la imagen** a un servicio en la nube (ImgBB o alternativo)
3. **Proporciona una URL** para escanear el código desde el teléfono
4. **Espera automáticamente** hasta que se complete la autenticación

## Características

- **Detección automática**: Detecta cuando WhatsApp Web requiere autenticación
- **Captura inteligente**: Toma screenshot solo del canvas del código QR
- **Subida a la nube**: Sube la imagen a ImgBB o servicio alternativo
- **URL temporal**: Proporciona enlace directo para escanear
- **Espera inteligente**: Espera hasta que se complete la autenticación
- **Limpieza automática**: Elimina archivos temporales después del uso

## Configuración

### 1. API Key de ImgBB (Opcional pero recomendado)

Para usar ImgBB (servicio principal):

1. Ve a [https://api.imgbb.com/](https://api.imgbb.com/)
2. Regístrate y obtén tu API key gratuita
3. Edita `config/api_keys.py`:
```python
IMGBB_API_KEY = "tu_api_key_aqui"
```

**Nota**: ImgBB es gratuito con límite de 1000 requests/mes.

### 2. Servicios Alternativos

Si no configuras ImgBB, el sistema usará automáticamente:
- **PostImages.org**: Servicio alternativo gratuito
- **Ruta local**: Como último recurso, usa la ruta del archivo local

## Uso

### Automático (Recomendado)

El sistema maneja la autenticación automáticamente en los métodos `open_chat()` y `open_group()`:

```python
from modules.web_manager import WebHandler

web_handler = WebHandler(browser="chrome")
web_handler.start()

# El sistema detectará automáticamente si se necesita QR
success = web_handler.open_chat("3027032694", "Hola")
if success:
    print("Chat abierto exitosamente")
else:
    print("Error al abrir chat")
```

### Manual

También puedes manejar la autenticación manualmente:

```python
from core.qr_handler import QRCodeHandler

# Crear manejador de QR
qr_handler = QRCodeHandler(driver)

# Verificar si se necesita autenticación
if not qr_handler.is_logged_in():
    # Manejar autenticación completa
    success = qr_handler.handle_qr_authentication()
    if success:
        print("Autenticación exitosa")
    else:
        print("Error en autenticación")
```

## Flujo de Autenticación

1. **Detección**: El sistema verifica si WhatsApp Web requiere QR
2. **Captura**: Toma screenshot del canvas del código QR
3. **Subida**: Sube la imagen a ImgBB o servicio alternativo
4. **Notificación**: Muestra la URL en los logs
5. **Espera**: Espera hasta que se complete el escaneo
6. **Verificación**: Confirma que la autenticación fue exitosa
7. **Limpieza**: Elimina archivos temporales

## Logs de Ejemplo

```
📱 WhatsApp Web requiere autenticación con código QR
📱 Detectando código QR de WhatsApp Web...
📸 Captura del código QR guardada en: temp/qr_code_20240115_143025.png
✅ Código QR subido exitosamente: https://i.ibb.co/example/qr_code.png
📱 CÓDIGO QR DISPONIBLE PARA ESCANEAR:
🔗 URL: https://i.ibb.co/example/qr_code.png
📱 Abre WhatsApp en tu teléfono y escanea el código QR
⏳ El sistema esperará hasta que escanees el código...
⏳ Esperando escaneo del código QR...
✅ Código QR escaneado exitosamente
✅ Sesión de WhatsApp Web activa
```

## Estructura de Archivos

```
core/
├── qr_handler.py          # Manejador principal del código QR
└── logger_config.py       # Configuración de logging

config/
└── api_keys.py           # Configuración de API keys

temp/                     # Archivos temporales (auto-creado)
└── qr_code_*.png        # Capturas temporales del QR

docs/
└── QR_AUTHENTICATION.md  # Esta documentación
```

## Pruebas

Para probar la funcionalidad:

```bash
# Prueba de captura de QR (modo headless)
python test_qr_handler.py

# Prueba completa con navegador
# Descomenta la línea en test_qr_handler.py
```

## Solución de Problemas

### Error: "No se encontró el canvas del código QR"
- **Causa**: WhatsApp Web cambió la estructura de la página
- **Solución**: Actualizar los selectores en `qr_handler.py`

### Error: "API Key no configurada"
- **Causa**: No se configuró la API key de ImgBB
- **Solución**: Configurar API key o el sistema usará servicios alternativos

### Error: "Código QR expirado"
- **Causa**: El código QR expiró antes de ser escaneado
- **Solución**: El sistema detectará esto automáticamente y mostrará un nuevo QR

### Error: "Timeout esperando escaneo"
- **Causa**: No se escaneó el código QR en 5 minutos
- **Solución**: Verificar la URL del QR y escanear desde el teléfono

## Personalización

### Cambiar timeout de espera

En `core/qr_handler.py`:
```python
def wait_for_qr_scan(self, timeout=300):  # 5 minutos por defecto
```

### Agregar nuevos servicios de subida

En `core/qr_handler.py`, método `_upload_to_temp_service()`:
```python
# Agregar nuevo servicio
try:
    # Tu código para nuevo servicio
    pass
except Exception as e:
    logger.error(f"Error con nuevo servicio: {e}")
```

### Modificar selectores de detección

En `core/qr_handler.py`, método `not qr_handler.is_logged_in()`:
```python
qr_selectors = [
    "//canvas[@aria-label='Scan me!']",
    # Agregar nuevos selectores aquí
]
```

## Seguridad

- **Archivos temporales**: Se eliminan automáticamente después del uso
- **URLs temporales**: Las imágenes se suben a servicios públicos
- **Logs**: No se guardan URLs de imágenes en logs permanentes
- **API Keys**: Se almacenan en archivo de configuración separado

## Limitaciones

- **ImgBB**: 1000 requests/mes gratuitos
- **PostImages**: Sin límite conocido pero puede ser lento
- **Detección**: Depende de la estructura actual de WhatsApp Web
- **Timeout**: Máximo 5 minutos para escanear (configurable) 