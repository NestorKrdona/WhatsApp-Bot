import os
import sys
from loguru import logger
from datetime import datetime

def setup_logger():
    """
    Configura loguru para guardar logs en archivos diarios con rotación.
    Los logs se guardan en la carpeta 'logs' con formato diario.
    """
    # Crear directorio de logs si no existe
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Remover el handler por defecto (consola)
    logger.remove()
    
    # Configurar formato de log
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Handler para consola (solo INFO y superior)
    # logger.add(
    #     sys.stdout,
    #     format=log_format,
    #     level="INFO",
    #     colorize=True,
    #     backtrace=True,
    #     diagnose=True
    # )
    
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG",
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    
    # Handler para archivo de logs diario (todos los niveles)
    logger.add(
        os.path.join(logs_dir, "whatsapp_bot_{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="DEBUG",
        rotation="00:00",  # Rotación diaria a medianoche
        retention="30 days",  # Mantener logs por 30 días
        compression="zip",  # Comprimir archivos antiguos
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )
    
    # Handler para archivo de errores (solo ERROR y superior)
    logger.add(
        os.path.join(logs_dir, "errors_{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="90 days",  # Mantener errores por más tiempo
        compression="zip",
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )
    
    logger.info("🔧 Configuración de logging inicializada")
    logger.info(f"📁 Logs guardados en: {logs_dir}")

def get_logger():
    """
    Retorna el logger configurado.
    """
    return logger 