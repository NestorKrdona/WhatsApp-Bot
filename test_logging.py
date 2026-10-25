#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de logging con loguru.
Este script genera diferentes tipos de logs para probar la funcionalidad.
"""

import os
import time
from core.logger_config import setup_logger
from loguru import logger

def test_logging():
    """Prueba diferentes niveles y tipos de logging."""
    
    # Configurar logging
    setup_logger()
    
    logger.info("🚀 Iniciando prueba del sistema de logging...")
    
    # Probar diferentes niveles de logging
    logger.debug("Este es un mensaje de DEBUG - solo visible en archivos")
    logger.info("Este es un mensaje de INFO - visible en consola y archivos")
    logger.warning("⚠️ Este es un mensaje de WARNING")
    logger.error("❌ Este es un mensaje de ERROR")
    logger.critical("🚨 Este es un mensaje CRÍTICO")
    
    # Simular logs del sistema WhatsApp
    logger.info("🌐 Iniciando el proceso de envío de mensajes...")
    logger.info("📱 Conectando con WhatsApp Web...")
    logger.info("✅ Mensaje enviado exitosamente")
    
    # Simular errores
    try:
        # Simular una operación que podría fallar
        raise Exception("Error de conexión con WhatsApp")
    except Exception as e:
        logger.error(f"💔 Error al enviar mensaje: {e}")
    
    # Simular logs de tickets
    logger.info("📩 Ticket recibido: ID-12345")
    logger.info("🔍 Procesando ticket 📲 3027032694 con chrome")
    logger.info("✅ Ticket 📲 3027032694 finalizado")
    
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
    
    logger.info("✅ Prueba del sistema de logging completada")
    
    # Mostrar información sobre la configuración
    logger.info("📋 Configuración del sistema de logging:")
    logger.info("   - Rotación diaria a medianoche")
    logger.info("   - Retención: 30 días para logs normales")
    logger.info("   - Retención: 90 días para errores")
    logger.info("   - Compresión automática en ZIP")

if __name__ == "__main__":
    test_logging() 