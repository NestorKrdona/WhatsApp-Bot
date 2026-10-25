# Sistema de Logging con Loguru

## Descripción

El proyecto ahora utiliza **Loguru** para un sistema de logging avanzado que guarda todos los logs en archivos diarios con rotación automática.

## Características

- **Rotación diaria**: Los archivos de log se crean automáticamente cada día
- **Retención configurable**: Los logs se mantienen por 30 días, los errores por 90 días
- **Compresión automática**: Los archivos antiguos se comprimen en formato ZIP
- **Múltiples niveles**: Logs completos y archivo separado solo para errores
- **Formato detallado**: Incluye timestamp, nivel, módulo, función y línea

## Estructura de Archivos

```
logs/
├── whatsapp_bot_2024-01-15.log    # Logs completos del día
├── whatsapp_bot_2024-01-16.log    # Logs completos del día siguiente
├── errors_2024-01-15.log          # Solo errores del día
├── errors_2024-01-16.log          # Solo errores del día siguiente
└── whatsapp_bot_2024-01-14.log.zip  # Archivos comprimidos antiguos
```

## Configuración

La configuración se encuentra en `core/logger_config.py`:

- **Logs completos**: Nivel DEBUG y superior
- **Logs de consola**: Nivel INFO y superior (con colores)
- **Logs de errores**: Solo nivel ERROR y superior
- **Retención**: 30 días para logs normales, 90 días para errores

## Uso

### En cualquier módulo del proyecto:

```python
from loguru import logger

# Diferentes niveles de logging
logger.debug("Mensaje de debug")
logger.info("Mensaje informativo")
logger.warning("Advertencia")
logger.error("Error")
logger.critical("Error crítico")

# Logging con contexto
logger.info(f"Procesando ticket {ticket_id}")
```

### Formato de los logs:

```
2024-01-15 14:30:25.123 | INFO     | web_manager:execute:85 | 🌐 Iniciando el proceso de envío de mensajes...
2024-01-15 14:30:26.456 | ERROR    | queue_manager:process_ticket:44 | ❌ [chrome] Error al procesar ticket 📲 3027032694: Connection timeout
```

## Ventajas

1. **Organización**: Logs separados por día para fácil navegación
2. **Rendimiento**: Rotación automática evita archivos muy grandes
3. **Espacio**: Compresión automática ahorra espacio en disco
4. **Debugging**: Información detallada para troubleshooting
5. **Monitoreo**: Archivo separado de errores para alertas

## Inicialización

El sistema se inicializa automáticamente en `main.py`:

```python
from core.logger_config import setup_logger

if __name__ == '__main__':
    setup_logger()  # Configura logging antes de iniciar
    asyncio.run(main())
```

## Personalización

Para modificar la configuración, edita `core/logger_config.py`:

- Cambiar el directorio de logs
- Modificar el formato de los mensajes
- Ajustar la retención de archivos
- Cambiar los niveles de logging
- Agregar nuevos handlers 