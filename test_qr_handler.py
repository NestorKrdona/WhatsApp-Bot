#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad del manejo de código QR.
Este script simula el proceso de autenticación de WhatsApp Web.
"""

import os
import time
from core.logger_config import setup_logger
from loguru import logger
from modules.web_manager import WebHandler

def test_qr_authentication():
    """Prueba la funcionalidad de autenticación con código QR."""
    
    # Configurar logging
    setup_logger()
    
    logger.info("🚀 Iniciando prueba de autenticación con código QR...")
    
    try:
        # Crear instancia del WebHandler
        web_handler = WebHandler(browser="chrome")
        
        # Iniciar el navegador
        web_handler.start()
        logger.info("🌐 Navegador iniciado correctamente")
        
        # Navegar a WhatsApp Web
        web_handler.driver.get("https://web.whatsapp.com")
        logger.info("📱 Navegando a WhatsApp Web...")
        
        # Esperar un momento para que cargue la página
        time.sleep(3)
        
        # Verificar si se necesita autenticación QR
        if web_handler.handle_whatsapp_authentication():
            logger.info("✅ Autenticación exitosa o no requerida")
        else:
            logger.error("❌ Falló la autenticación")
        
        # Cerrar navegador
        web_handler.exit()
        logger.info("🟢 Navegador cerrado correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error durante la prueba: {e}")
        return False
    
    logger.info("✅ Prueba de autenticación QR completada")
    return True

def test_qr_capture():
    """Prueba solo la captura del código QR."""
    
    setup_logger()
    logger.info("📸 Probando captura de código QR...")
    
    try:
        from core.qr_handler import QRCodeHandler
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # Configurar Chrome en modo headless para la prueba
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navegar a WhatsApp Web
        driver.get("https://web.whatsapp.com")
        time.sleep(3)
        
        # Crear manejador de QR
        qr_handler = QRCodeHandler(driver)
        
        # Verificar si se necesita QR
        if not qr_handler.is_logged_in():
            logger.info("📱 Código QR detectado")
            
            # Intentar capturar
            qr_path = qr_handler.capture_qr_code()
            if qr_path:
                logger.info(f"✅ Captura exitosa: {qr_path}")
                
                # Intentar subir
                qr_url = qr_handler.upload_to_imgbb(qr_path)
                logger.info(f"🔗 URL del código QR: {qr_url}")
                
                # Limpiar archivo temporal
                if os.path.exists(qr_path):
                    os.remove(qr_path)
            else:
                logger.error("❌ No se pudo capturar el código QR")
        else:
            logger.info("✅ No se requiere código QR")
        
        driver.quit()
        
    except Exception as e:
        logger.error(f"❌ Error en prueba de captura: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("🧪 Iniciando pruebas del sistema de código QR...")
    
    # Ejecutar pruebas
    test_qr_capture()
    # test_qr_authentication()  # Descomenta para probar con navegador completo
    
    logger.info("✅ Todas las pruebas completadas") 