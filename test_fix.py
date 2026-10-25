#!/usr/bin/env python3
"""
Script de prueba para verificar que todas las correcciones de logging funcionan correctamente.
"""

import os
import sys
from core.logger_config import setup_logger
from loguru import logger

def test_logging_fix():
    """Prueba que todas las funciones de logging funcionan correctamente."""
    
    # Configurar logging
    setup_logger()
    
    logger.info("🚀 Iniciando prueba de corrección de logging...")
    
    # Probar diferentes niveles de logging
    logger.debug("Este es un mensaje de DEBUG")
    logger.info("Este es un mensaje de INFO")
    logger.warning("⚠️ Este es un mensaje de WARNING")
    logger.error("❌ Este es un mensaje de ERROR")
    logger.critical("🚨 Este es un mensaje CRÍTICO")
    
    # Probar logging con emojis y formato
    logger.info("📱 WhatsApp Bot - Sistema funcionando correctamente")
    logger.info("🌐 Navegador iniciado exitosamente")
    logger.info("✅ Mensaje enviado correctamente")
    
    # Probar logging de errores
    try:
        # Simular un error
        raise Exception("Error de prueba para verificar logging")
    except Exception as e:
        logger.error(f"💔 Error capturado: {e}")
    
    logger.info("✅ Prueba de corrección de logging completada exitosamente")
    
    # Verificar que se creó el directorio de logs
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if os.path.exists(logs_dir):
        logger.info(f"📁 Directorio de logs creado correctamente: {logs_dir}")
        
        # Listar archivos de log creados
        log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
        if log_files:
            logger.info(f"📄 Archivos de log creados: {log_files}")
        else:
            logger.warning("⚠️ No se encontraron archivos de log")
    else:
        logger.error("❌ No se pudo crear el directorio de logs")

if __name__ == "__main__":
    test_logging_fix() 