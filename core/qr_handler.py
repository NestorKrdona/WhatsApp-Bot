import os
import time
import base64
import requests
from datetime import datetime
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class QRCodeHandler:
    """
    Maneja la captura y subida del código QR de WhatsApp Web
    cuando la sesión está cerrada.
    """
    
    def __init__(self, driver):
        self.driver = driver
        # Intentar cargar API key desde configuración
        try:
            from config.api_keys import IMGBB_API_KEY
            self.imgbb_api_key = IMGBB_API_KEY
        except ImportError:
            self.imgbb_api_key = "YOUR_IMGBB_API_KEY"  # Valor por defecto
        
    # def is_qr_code_required(self):
    #     """
    #     Verifica si WhatsApp Web requiere escanear un código QR.
    #     """
    #     try:
    #         return False if self.wait_element((By.XPATH, "//span[@data-icon='wa-wordmark']"), timeout=2, type="exist") else True
    #     except:
    #         return False
    

    def is_logged_in_ui(self, timeout=2):
        """
        Comprueba si la sesión está logueada mirando UI visible:
        - input de mensaje (contenteditable) visible
        - o panel de chats visible (pane-side)
        Devuelve True si parece logueado.
        """
        driver = self.driver

        # 1) Input de mensaje visible (busca cualquier div contenteditable que haga referencia a "message/mensaje/escribir")
        try:
            script = """
            var nodes = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
            for (var i=0;i<nodes.length;i++){
                var el = nodes[i];
                var text = (el.getAttribute('title') || el.getAttribute('aria-label') || '').toLowerCase();
                // palabras comunes en inglés/español que aparecen en el input
                if (text.includes('message') || text.includes('mensaje') || text.includes('type a message') || text.includes('escribir')) {
                    var rect = el.getBoundingClientRect();
                    // visible y tamaño razonable
                    if (rect.width > 10 && rect.height > 10 && window.getComputedStyle(el).visibility !== 'hidden') return true;
                }
            }
            return false;
            """
            if driver.execute_script(script):
                return True
        except Exception:
            pass

        # 2) Panel de chats visible (id pane-side)
        try:
            WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.ID, "pane-side")))
            return True
        except TimeoutException:
            pass
        except Exception:
            pass

        return False
    
    def is_qr_canvas_visible(self):
        """Devuelve True si el canvas del QR existe y es visible en pantalla."""
        driver = self.driver
        script = """
        var c = document.querySelector('canvas[aria-label="Scan this QR code to link a device!"], canvas[aria-label^="Scan this QR"]');
        if(!c) return false;
        var style = window.getComputedStyle(c);
        if(style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) === 0) return false;
        var r = c.getBoundingClientRect();
        if(r.width < 10 || r.height < 10) return false;
        // comprobar que está dentro del viewport
        if(r.bottom < 0 || r.right < 0 || r.top > (window.innerHeight || document.documentElement.clientHeight)) return false;
        return true;
        """
        try:
            return bool(self.driver.execute_script(script))
        except Exception:
            return False

    def has_auth_storage(self):
        driver = self.driver
        try:
            # localStorage keys
            keys = driver.execute_script("return Object.keys(window.localStorage || {});")
            # buscar claves típicas o tokens largos
            for k in keys:
                if 'WAToken' in k or 'WABrowserId' in k or 'WASecretBundle' in k or len(driver.execute_script("return window.localStorage.getItem(arguments[0])", k) or "") > 100:
                    return True
        except Exception:
            pass

        # IndexedDB (async)
        try:
            script = """
            var cb = arguments[arguments.length - 1];
            if(!indexedDB || !indexedDB.databases) return cb([]);
            indexedDB.databases().then(function(dbs){ cb(dbs.map(function(d){ return d.name; })); }).catch(function(){ cb([]); });
            """
            names = driver.execute_async_script(script)
            # si hay bases con nombres sospechosos (puedes imprimirlas)
            if names and len(names) > 0:
                return True
        except Exception:
            pass

        return False

    
        
    # def is_qr_code_required(self):
    #     """
    #     Verifica si WhatsApp Web requiere escanear un código QR visible.
    #     """
    #     try:
    #         qr_visible = WebDriverWait(self.driver, 20).until(
    #             EC.visibility_of_element_located(
    #                 (By.XPATH, "//canvas[@aria-label='Scan this QR code to link a device!']")
    #             )
    #         )
    #         return qr_visible is not None
    #     except:
    #         return False
        
    def is_logged_in(self, timeout=3):
        """
        Determina si la sesión de WhatsApp Web está activa.
        """
        driver = self.driver
        logger.debug("🔍 Comprobando si la sesión de WhatsApp Web está activa...")

        # 1) Si hay panel de chats visible
        try:
            WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.ID, "pane-side"))
            )
            logger.debug("✅ Panel de chats encontrado → sesión activa.")
            return True
        except TimeoutException:
            logger.debug("❌ Panel de chats no visible.")

        # 2) Si hay input de mensaje visible
        try:
            script = """
            var nodes = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
            for (var el of nodes) {
                var label = (el.getAttribute('aria-label') || el.getAttribute('title') || '').toLowerCase();
                if (label.includes('mensaje') || label.includes('message') || label.includes('escribir') || label.includes('type a message')) {
                    var r = el.getBoundingClientRect();
                    if (r.width > 10 && r.height > 10) return true;
                }
            }
            return false;
            """
            if driver.execute_script(script):
                logger.debug("✅ Input de mensaje encontrado → sesión activa.")
                return True
            else:
                logger.debug("❌ Input de mensaje no encontrado.")
        except Exception as e:
            logger.error(f"Error comprobando input de mensaje: {e}")

        # 3) Si QR visible → sesión cerrada
        try:
            script = """
            var c = document.querySelector('canvas[aria-label*="QR"]');
            if (!c) return false;
            var r = c.getBoundingClientRect();
            return r.width > 10 && r.height > 10;
            """
            if driver.execute_script(script):
                logger.debug("⚠️ Código QR visible → sesión cerrada.")
                return False
        except Exception as e:
            logger.error(f"Error comprobando canvas QR: {e}")

        # 4) Revisar localStorage
        try:
            keys = driver.execute_script("return Object.keys(window.localStorage || {});")
            if any(k for k in keys if 'WAToken' in k or 'WASecretBundle' in k):
                logger.debug("✅ Claves de sesión encontradas en localStorage → posible sesión activa.")
                return True
            else:
                logger.debug("❌ No se encontraron claves de sesión en localStorage.")
        except Exception as e:
            logger.error(f"Error comprobando localStorage: {e}")

        logger.debug("⚠️ No se detectaron señales de sesión activa.")
        return False
    
    def capture_qr_code(self):
        """
        Captura un screenshot de toda la página de WhatsApp Web.
        """
        try:
            logger.info("📱 Tomando captura completa de WhatsApp Web...")

            # Crear directorio temporal si no existe
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
            os.makedirs(temp_dir, exist_ok=True)

            # Guardar screenshot de toda la página
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(temp_dir, f"whatsapp_web_{timestamp}.png")
            
            self.driver.save_screenshot(temp_path)

            logger.info(f"📸 Captura de toda la página guardada en: {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"❌ Error al capturar pantalla completa: {e}")
            return None

    
    def upload_to_imgbb(self, image_path):
        """
        Sube la imagen del código QR a ImgBB y retorna la URL.
        """
        try:
            if not self.imgbb_api_key or self.imgbb_api_key == "YOUR_IMGBB_API_KEY":
                logger.warning("⚠️ API Key de ImgBB no configurada. Usando método alternativo...")
                return self._upload_to_temp_service(image_path)
            
            # Leer imagen y convertir a base64
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Preparar datos para ImgBB
            files = {
                'image': ('qr_code.png', image_data, 'image/png')
            }
            
            data = {
                'key': self.imgbb_api_key
            }
            
            # Subir a ImgBB
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    image_url = result['data']['url']
                    logger.info(f"✅ Código QR subido exitosamente: {image_url}")
                    return image_url
                else:
                    logger.error(f"❌ Error en respuesta de ImgBB: {result}")
            else:
                logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error al subir imagen a ImgBB: {e}")
        
        # Fallback a método alternativo
        return self._upload_to_temp_service(image_path)
    
    def _upload_to_temp_service(self, image_path):
        """
        Método alternativo usando un servicio temporal diferente.
        """
        try:
            # Usar postimages.org como alternativa
            with open(image_path, "rb") as f:
                files = {'file': f}
                response = requests.post(
                    "https://postimages.org/json/rr",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'OK':
                    image_url = result['data']['url']
                    logger.info(f"✅ Código QR subido a servicio alternativo: {image_url}")
                    return image_url
                    
        except Exception as e:
            logger.error(f"❌ Error con servicio alternativo: {e}")
        
        # Si todo falla, retornar la ruta local
        logger.warning("⚠️ No se pudo subir la imagen. Usando ruta local.")
        return f"file://{os.path.abspath(image_path)}"
    
    def wait_for_qr_scan(self, timeout=300):
        """
        Espera a que se escanee el código QR y se complete la autenticación.
        """
        logger.info("⏳ Esperando escaneo del código QR...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Verificar si ya no se necesita el QR (usuario autenticado)
                if self.is_logged_in():
                    logger.info("✅ Código QR escaneado exitosamente")
                    return True
                
                # Verificar si hay mensaje de error
                error_selectors = [
                    "//div[contains(text(), 'QR code expired')]",
                    "//div[contains(text(), 'Código QR expirado')]",
                    "//div[contains(text(), 'QR code has expired')]"
                ]
                
                for selector in error_selectors:
                    try:
                        error_element = self.driver.find_element(By.XPATH, selector)
                        if error_element:
                            logger.warning("⚠️ Código QR expirado")
                            return False
                    except:
                        pass
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error durante espera del QR: {e}")
                time.sleep(2)
        
        logger.error("❌ Timeout esperando escaneo del código QR")
        return False
    
    def handle_qr_authentication(self):
        """
        Maneja el proceso completo de autenticación con código QR.
        """
        if self.is_logged_in():
            logger.info("✅ Sesión de WhatsApp Web activa")
            return True
        
        logger.warning("⚠️ Sesión de WhatsApp Web cerrada. Se requiere código QR.")
        
        # Capturar código QR
        qr_image_path = self.capture_qr_code()
        if not qr_image_path:
            logger.error("❌ No se pudo capturar el código QR")
            return False
        
        # Subir imagen a la nube
        # qr_url = self.upload_to_imgbb(qr_image_path)
        qr_url = "NO ESTA ACTIVADO"
        
        # Mostrar información al usuario
        logger.info("📱 CÓDIGO QR DISPONIBLE PARA ESCANEAR:")
        logger.info(f"🔗 URL: {qr_url}")
        logger.info("📱 Abre WhatsApp en tu teléfono y escanea el código QR")
        logger.info("⏳ El sistema esperará hasta que escanees el código...")
        
        # Esperar escaneo
        success = self.wait_for_qr_scan()
        
        # Limpiar archivo temporal
        try:
            if os.path.exists(qr_image_path):
                os.remove(qr_image_path)
                logger.debug("🗑️ Archivo temporal del QR eliminado")
        except:
            pass
        
        return success 
    
    
class ScreenCaptureUploader:
    """
    Clase para tomar capturas de pantalla y subirlas a un servicio de hosting de imágenes.
    Ideal para generar evidencias cuando algo falla.
    """

    def __init__(self, driver, imgbb_api_key=None):
        self.driver = driver
        try:
            if not imgbb_api_key:
                from config.api_keys import IMGBB_API_KEY
                self.imgbb_api_key = IMGBB_API_KEY
            else:
                self.imgbb_api_key = imgbb_api_key
        except ImportError:
            self.imgbb_api_key = "YOUR_IMGBB_API_KEY"

    def take_screenshot(self, prefix="screenshot"):
        """
        Toma una captura completa de la pantalla y la guarda en /temp.
        """
        try:
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
            os.makedirs(temp_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(temp_dir, f"{prefix}_{timestamp}.png")

            self.driver.save_screenshot(file_path)
            logger.info(f"📸 Captura de pantalla guardada en: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"❌ Error al tomar captura de pantalla: {e}")
            return None

    def upload_to_imgbb(self, image_path):
        """
        Sube la imagen a ImgBB o a un servicio alternativo si no hay API Key.
        """
        if not image_path or not os.path.exists(image_path):
            logger.error("❌ No se encontró el archivo para subir.")
            return None

        try:
            if not self.imgbb_api_key or self.imgbb_api_key == "YOUR_IMGBB_API_KEY":
                logger.warning("⚠️ API Key de ImgBB no configurada. Usando método alternativo...")
                return self._upload_to_temp_service(image_path)

            with open(image_path, "rb") as f:
                image_data = f.read()

            files = {
                'image': ('error_screenshot.png', image_data, 'image/png')
            }
            data = {
                'key': self.imgbb_api_key
            }

            response = requests.post("https://api.imgbb.com/1/upload", files=files, data=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    image_url = result['data']['url']
                    logger.info(f"✅ Captura subida a ImgBB: {image_url}")
                    return image_url
                else:
                    logger.error(f"❌ Respuesta inválida de ImgBB: {result}")
            else:
                logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error al subir a ImgBB: {e}")

        return self._upload_to_temp_service(image_path)

    def _upload_to_temp_service(self, image_path):
        """
        Servicio alternativo en caso de que no haya API Key o ImgBB falle.
        """
        try:
            with open(image_path, "rb") as f:
                files = {'file': f}
                response = requests.post(
                    "https://postimages.org/json/rr",
                    files=files,
                    timeout=30
                )

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'OK':
                    image_url = result['data']['url']
                    logger.info(f"✅ Captura subida a servicio alternativo: {image_url}")
                    return image_url
        except Exception as e:
            logger.error(f"❌ Error con servicio alternativo: {e}")

        logger.warning("⚠️ No se pudo subir la captura. Retornando ruta local.")
        return f"file://{os.path.abspath(image_path)}"

    def capture_and_upload(self, prefix="error_screenshot"):
        """
        Método directo: toma captura y la sube.
        Retorna la URL o la ruta local.
        """
        path = self.take_screenshot(prefix)
        if path:
            return self.upload_to_imgbb(path)
        return None