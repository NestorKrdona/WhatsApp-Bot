import os
import time
import platform
import psutil
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.opera import OperaDriverManager
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from core.utils import sanitize_phone, encode_text
from abc import ABC, abstractmethod
import shutil
from core.qr_handler import QRCodeHandler, ScreenCaptureUploader
import subprocess


PROFILE_NAME = "WhatsAppBot"

# Suprimir logs de webdriver_manager, selenium y Chrome
# os.environ["WDM_LOG"] = "0"
# os.environ["WDM_PRINT_FIRST_LINE"] = "False"
# os.environ["WDM_PRINT_LOG"] = "False"
# logger.remove()
# logger.add(lambda msg: None, level="DEBUG")

class BaseWebHandler(ABC):
    browser_name = None
    process_names = []
    driver_names = []

    def __init__(self):
        self.driver = None
        self.profile_dir = None

    @abstractmethod
    def start():
        pass

    def check_processes(self):
        for process in psutil.process_iter(attrs=["pid", "name"]):
            name = process.info["name"].lower()
            for pname in self.process_names:
                if pname in name:
                    logger.info(f"{self.browser_name} aún está corriendo: PID {process.info['pid']}")

    def kill(self):
        for process in psutil.process_iter(['pid', 'name']):
            name = process.info['name']
            if name:
                for pname in self.process_names + self.driver_names:
                    if pname.lower() in name.lower():
                        try:
                            psutil.Process(process.info['pid']).kill()
                            logger.info(f"🔪 Proceso {name} (PID {process.info['pid']}) eliminado.")
                        except Exception as e:
                            logger.warning(f"⚠️ No se pudo matar el proceso {name}: {e}")

    def get_profile_dir(self, browser):
        base_dir = os.path.join(os.path.dirname(__file__), "browser_profiles")
        os.makedirs(base_dir, exist_ok=True)
        profile_dir = os.path.join(base_dir, f"{PROFILE_NAME}_{browser}_v1")
        os.makedirs(profile_dir, exist_ok=True)
        return profile_dir

    def exit(self):
        """Cerrar el navegador y liberar los recursos"""
        if self.driver:
            self.driver.quit()
            logger.warning("Se cerró el Web Driver")
        if self.profile_dir and "tmp" in self.profile_dir:
            try:
                shutil.rmtree(self.profile_dir)
                logger.info(f"🧹 Carpeta temporal eliminada: {self.profile_dir}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar carpeta temporal: {e}")

    def wait_element(self, element, timeout=30, type="exist"):
        """Función auxiliar para esperar un elemento en la página y verificar si es clickeable y existe."""
        logger.debug(f"Se está comprobando {type} al elemento {element}")
        try:
            return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(element)) if type == "click" \
            else WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(element))
        except: return None

    def handle_whatsapp_authentication(self):
        """
        Maneja la autenticación de WhatsApp Web, incluyendo el código QR si es necesario.
        """
        if not self.driver:
            logger.error("❌ Driver no inicializado")
            return False
        
        try:
            # Crear manejador de QR
            qr_handler = QRCodeHandler(self.driver)
            
            # Verificar si se necesita autenticación QR
            if not qr_handler.is_logged_in():
                logger.info("📱 WhatsApp Web requiere autenticación con código QR")
                return qr_handler.handle_qr_authentication()
            else:
                logger.info("✅ WhatsApp Web ya está autenticado")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error en autenticación de WhatsApp: {e}")
            return False

    def execute(self, message, number="3027032694", pdf_path=None, test=False):
        self.start()
        logger.info("🌐 Iniciando el proceso de envío de mensajes...")
        try:
            # Abrir chat o grupo
            if test:
                success = self.open_group("Grupo de Pruebas - WhatsApp Bot")
            else:
                success = self.open_chat(number, message)
            
            if not success:
                logger.error("❌ No se pudo abrir el chat/grupo")
                return False
            
            # Enviar archivo PDF si se proporciona
            if pdf_path:
                self.send_pdf(pdf_path)
            
            # Enviar mensaje
            if test or not pdf_path:
                self.send_message(message, only_send=bool(not test))
            
            sc = ScreenCaptureUploader(self.driver)
            if "link de pago" in message: 
                image_url = sc.capture_and_upload("envio_exitoso")
                logger.info(f"📷 Captura subida: {image_url}")
            logger.info("✅ Mensaje enviado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error detectado: {e}")
            sc = ScreenCaptureUploader(self.driver)
            image_url = sc.capture_and_upload("error_detectado")
            logger.error(f"📷 Captura subida: {image_url}")
            logger.error(f"💔 Error al enviar mensaje: {e}")
            return False
        finally:
            logger.info("✅ Proceso finalizado, cerrando navegador...")
            time.sleep(2)
            self.exit()
            logger.info("🟢 Navegador cerrado correctamente.")
            
    def skip_alert(self):
        """Funcion auxiliar para saltar alerta emergente"""
        try:
            try: self.wait_element((By.XPATH, '//div[contains(text(), "Continue")]'), 1, type="click").click()
            except: self.wait_element((By.XPATH, '//div[contains(text(), "Continuar")]'), 1, type="click").click()
        except: pass
        time.sleep(1)
    
    def verify_pdf_upload(self, timeout=1, state=None):
        state = self.wait_element((By.XPATH, '//div[contains(text(), "No preview available")]'), timeout=timeout, type="exist")
        state = state or self.wait_element((By.XPATH, "//div[@data-js-attach-preview='true']"), timeout=timeout, type="exist")
        state = state or self.wait_element((By.XPATH, '//div[contains(text(), "No hay vista previa disponible")]'), timeout=timeout, type="exist")
        if state: logger.info("✅ PDF cargado correctamente.") ; return 
        self.verify_pdf_upload(timeout=timeout*2, state=state)
        
    def send_pdf(self, pdf_path):
        original_path = pdf_path
        temp_path = None
        if pdf_path and "_" in os.path.basename(pdf_path):
            base = os.path.basename(pdf_path)
            parts = base.split("_")
            if len(parts) > 1 and parts[-1].endswith(".pdf"):
                original_name = "_".join(parts[:-1]) + ".pdf"
                temp_path = os.path.join(os.path.dirname(pdf_path), original_name)
                shutil.copy2(pdf_path, temp_path)
                pdf_path = temp_path
        try:self.wait_element((By.XPATH, "//span[@data-icon='plus-rounded']"), type="click").click()
        except:self.wait_element((By.XPATH, "//span[@data-icon='plus']"), type="click").click()
        file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(pdf_path)
        self.verify_pdf_upload()
        try: self.wait_element((By.XPATH, "//span[@data-icon='wds-ic-send-filled']"), type="exist")
        except: 
            try: self.wait_element((By.XPATH, "//span[@data-icon='send']"), type="exist")
            except: time.sleep(10)
        try: self.wait_element((By.XPATH, "//div[@aria-label='Enviar']"), type="click").click()
        except: self.wait_element((By.XPATH, "//div[@aria-label='Send']"), type="click").click()
        time.sleep(10)
        WebDriverWait(self.driver, 30).until(EC.invisibility_of_element_located((By.XPATH, "//span[@data-icon='audio-cancel-noborder']")))
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    def send_message(self, message, only_send=False):
        """Envía un mensaje de texto a través de WhatsApp Web."""
        try: message_box = self.wait_element((By.XPATH, "//div[@contenteditable='true' and @data-tab='10']"), type="exist")
        except: 
            try: message_box = self.wait_element((By.XPATH, "//div[@contenteditable='true' and @data-tab='6']"), type="exist", timeout=5)
            except: 
                try: message_box = self.wait_element((By.XPATH, "//div[@contenteditable='true' and @data-tab='1']"), type="exist", timeout=5)
                except: message_box = self.wait_element((By.XPATH, "//div[@contenteditable='true']"), type="exist", timeout=5)
        if not message_box: logger.error("❌ No se encontró el cuadro de mensaje") ; return
        if only_send: 
            message_box.send_keys(Keys.RETURN)
            time.sleep(10)
            return
        message_box.send_keys(message)
        message_box.send_keys(Keys.RETURN)
        time.sleep(10)

    # def open_chat(self, number, message="Mensaje enviado desde el bot de WhatsApp Web"):
    #     """Abre un chat de WhatsApp Web con un número específico."""
    #     url = f"https://web.whatsapp.com/send?phone={number}&text={message}"
    #     self.driver.get(url)
        
    #     # Verificar si se necesita autenticación QR
    #     if not self.handle_whatsapp_authentication():
    #         logger.error("❌ Falló la autenticación de WhatsApp Web")
    #         return False
        
    #     time.sleep(2)
        
    #     self.driver.get(url)
        
    #     # Esperar a que cargue la página del chat
    #     wait_chat = 120 if self.wait_element((By.XPATH, "//span[@data-icon='wa-wordmark']"), timeout=2, type="exist") else 300
    #     chat_loaded = self.wait_element((By.XPATH, "//div[@contenteditable='true']"), timeout=wait_chat, type="exist")
        
    #     if not chat_loaded:
    #         logger.error("❌ No se pudo cargar el chat de WhatsApp")
    #         return False
        
    #     self.skip_alert()
    #     logger.info(f"✅ Chat abierto exitosamente para el número {number}")
    #     return True
    
    def detect_invalid_number_modal(self, timeout=3):
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'El número de teléfono compartido a través de la dirección URL no es válido') or contains(text(), 'phone number shared in the URL is invalid')]"))
            )
            return el
        except: return None

    def open_chat(self, number, message="Mensaje enviado desde el bot de WhatsApp Web"):
        number = sanitize_phone(number)
        encoded = encode_text(message)
        urls_to_try = [
            f"https://web.whatsapp.com/send?phone={number}&text={encoded}",
            f"https://wa.me/{number}?text={encoded}",
            f"https://web.whatsapp.com/send?phone={number}"  # sin texto
        ]

        for url in urls_to_try:
            logger.info(f"🌐 Intentando abrir URL: {url}")
            try:
                self.driver.get(url)
                if not self.handle_whatsapp_authentication():
                    logger.error("❌ Falló la autenticación de WhatsApp Web")
                    return False
                time.sleep(2)
                wait_chat = 120 if self.wait_element((By.XPATH, "//span[@data-icon='wa-wordmark']"), timeout=2, type="exist") else 300
                chat_loaded = self.wait_element((By.XPATH, "//div[@contenteditable='true']"), timeout=wait_chat, type="exist")

                if self.detect_invalid_number_modal(timeout=2):
                    logger.warning("⚠️ Modal: número inválido detectado. Probando siguiente fallback.")
                    try:
                        ok_btn = self.driver.find_element(By.XPATH, "//div//button//span[text()='OK' or text()='Aceptar']")
                        ok_btn.click()
                    except: pass
                    time.sleep(1)
                    continue
                
                if chat_loaded:
                    self.skip_alert()
                    logger.info(f"✅ Chat abierto exitosamente para el número {number}")
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Error al abrir {url}: {e}")
                continue
        logger.error("❌ No se pudo abrir el chat por ningún url")
        return False

        
    def open_group(self, group_name):
        """Abre un grupo de WhatsApp Web por su nombre y envía un mensaje."""
        url = f"https://web.whatsapp.com"
        self.driver.get(url)
        
        # Verificar si se necesita autenticación QR
        if not self.handle_whatsapp_authentication():
            logger.error("❌ Falló la autenticación de WhatsApp Web")
            return False
        
        time.sleep(2)
        
        self.driver.get(url)
        # Esperar a que cargue la página principal
        wait_chat = 120 if self.wait_element((By.XPATH, "//span[@data-icon='wa-wordmark']"), timeout=2, type="exist") else 300
        group_element = self.wait_element((By.XPATH, f"//span[@title='{group_name}']"), timeout=wait_chat, type="exist")
        
        if not group_element:
            logger.error(f"👨‍👩‍👦‍👦 Grupo '{group_name}' no encontrado.")
            return False
        
        self.skip_alert()
        group_element.click()
        logger.info(f"✅ Grupo '{group_name}' abierto exitosamente")
        return True

class ChromeWebHandler(BaseWebHandler):
    browser_name = "Chrome"
    process_names = ["chrome"]
    driver_names = ["chromedriver"]
    
    def start(self):
        logger.info(f"🌐 Iniciando navegador Chrome...")
        self.check_processes()
        self.kill()
        
        
        subprocess.run(["pkill", "-f", "chrome.*selenium-profile"])

        # lock_path = "/usr/WhatsApp-Bot/modules/browser_profiles/WhatsAppBot_chrome/SingletonLock"
        # if os.path.exists(lock_path): os.remove(lock_path)
        
        base_profile = "/usr/WhatsApp-Bot/modules/browser_profiles/WhatsAppBot_chrome/"
        lock_files = ["SingletonLock", "SingletonSocket", "SingletonCookie"]
        for f in lock_files:
            path = os.path.join(base_profile, f)
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(f"Archivo de bloqueo eliminado: {path}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar {path}: {e}")

        USER_DATA_DIR = self.get_profile_dir("chrome")
        self.profile_dir = USER_DATA_DIR
        logger.info(f"📂 Ruta de perfil de usuario: {USER_DATA_DIR}")
        
        
        lock_path = os.path.join(USER_DATA_DIR, "SingletonLock")
        if os.path.exists(lock_path):
            logger.warning("🔒 El perfil está bloqueado (SingletonLock detectado).")
            self.check_processes()
            self.kill()
            time.sleep(1)  # Esperar a que se liberen procesos
            if os.path.exists(lock_path):
                os.remove(lock_path)
                logger.info("🗝️ SingletonLock eliminado manualmente.")
        
        
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        # chrome_options.add_argument("--profile-directory=Profile 1")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox") 
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disk-cache-size=524288000")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--enable-gpu-rasterization")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--media-cache-size=524288000")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-features=SSLVersionFallback,SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        # Primero intentar sin especificar binario
        try:
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("ℹ️  Iniciando Chrome sin especificar binario...")
        except Exception as e:
            logger.warning(f"⚠️  No se pudo iniciar Chrome: {e}")
            logger.info("ℹ️  Intentando con ruta de Ubuntu...")
            
            # Intentar con ruta de Ubuntu
            try:
                chrome_options.binary_location = "/usr/bin/google-chrome"  # Ubicación típica en Ubuntu
                logger.info(f"ℹ️  Usando Chrome desde {chrome_options.binary_location}")
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                logger.warning(f"⚠️  No se pudo encontrar Chrome en {chrome_options.binary_location}: {e}")
                logger.info("ℹ️  Continuando sin especificar binario...")

                # NO asignes None
                # chrome_options.binary_location = None  ❌ ELIMINA ESTA LÍNEA

                try:
                    service = ChromeService(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e:
                    logger.error(f"❌ No se pudo iniciar Chrome en ningún intento: {e}")
                    raise
        # 🚀 Simulación de conexión lenta (ejemplo: 3G)
        # self.driver.execute_cdp_cmd("Network.enable", {})
        # self.driver.execute_cdp_cmd(
        #     "Network.emulateNetworkConditions",
        #     {
        #         "offline": False,
        #         "latency": 2000,   # ms de delay
        #         "downloadThroughput": 50 * 1024 / 8,  # 500 kbps
        #         "uploadThroughput": 20 * 1024 / 8,    # 500 kbps
        #         "connectionType": "cellular2g"
        #     },
        # )
        # logger.info("🐢 Conexión lenta simulada (2G aprox).")

# Factory para elegir el navegador
class WebHandler:
    def __new__(cls, browser="chrome"):
        if browser == "firefox":
            return FirefoxWebHandler()
        if browser == "edge":
            return EdgeWebHandler()
        if browser == "chromium":
            return ChromiumWebHandler()
        if browser == "operagx":
            return OperaGXWebHandler()
        return ChromeWebHandler() 

class FirefoxWebHandler(BaseWebHandler):
    browser_name = "Firefox"
    process_names = ["firefox"]
    driver_names = ["geckodriver"]
    
    def start(self):
        logger.info(f"🌐 Iniciando navegador Firefox...")
        # self.check_processes()
        # self.kill()
        USER_DATA_DIR = self.get_profile_dir("firefox")
        self.profile_dir = USER_DATA_DIR
        logger.info(f"📂 Ruta de perfil de usuario: {USER_DATA_DIR}")
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument(f"-profile")
        firefox_options.add_argument(USER_DATA_DIR)
        # firefox_options.add_argument("-headless")
        firefox_options.set_preference("browser.cache.disk.capacity", 524288)
        firefox_options.set_preference("browser.cache.memory.capacity", 524288)
        firefox_options.set_preference("browser.cache.disk.enable", True)
        firefox_options.set_preference("browser.cache.memory.enable", True)
        firefox_options.set_preference("browser.privatebrowsing.autostart", False)
        firefox_options.set_preference("dom.webnotifications.enabled", False)
        firefox_options.set_preference("dom.push.enabled", False)
        firefox_options.set_preference("media.volume_scale", "0.0")
        
        # Primero intentar sin especificar binario
        try:
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            logger.info("ℹ️  Iniciando Firefox sin especificar binario...")
        except Exception as e:
            logger.warning(f"⚠️  No se pudo iniciar Firefox: {e}")
            logger.info("ℹ️  Intentando con ruta de Ubuntu...")
            
            # Intentar con ruta de Ubuntu
            try:
                firefox_options.binary_location = "/usr/bin/firefox"  # Ubicación típica en Ubuntu
                logger.info(f"ℹ️  Usando Firefox desde {firefox_options.binary_location}")
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=firefox_options)
            except Exception as e:
                logger.warning(f"⚠️  No se pudo encontrar Firefox en {firefox_options.binary_location}: {e}")
                logger.info("ℹ️  Continuando sin especificar binario...")
                firefox_options.binary_location = None
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=firefox_options)

class ChromiumWebHandler(BaseWebHandler):
    browser_name = "Chromium"
    process_names = ["chrome", "chromium"]
    driver_names = ["chromedriver"]

    def start(self):
        logger.info(f"🌐 Iniciando navegador Chromium...")
        USER_DATA_DIR = self.get_profile_dir("chromium")
        self.profile_dir = USER_DATA_DIR
        logger.info(f"📂 Ruta de perfil de usuario: {USER_DATA_DIR}")
        chromium_options = webdriver.ChromeOptions()
        chromium_options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        chromium_options.add_argument("--profile-directory=Profile 1")
        chromium_options.add_argument("--no-sandbox")
        chromium_options.add_argument("--disable-dev-shm-usage")
        chromium_options.add_argument("--disable-gpu")
        chromium_options.add_argument("--disable-logging")
        chromium_options.add_argument("--disk-cache-size=524288000")
        chromium_options.add_argument("--no-default-browser-check")
        chromium_options.add_argument("--ignore-certificate-errors")
        chromium_options.add_argument("--log-level=3")
        chromium_options.add_argument("--enable-gpu-rasterization")
        chromium_options.add_argument("--disable-background-networking")
        chromium_options.add_argument("--media-cache-size=524288000")
        chromium_options.add_argument("--disable-blink-features=AutomationControlled")
        chromium_options.add_argument("--disable-features=SSLVersionFallback,SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure")
        chromium_options.add_argument("--silent")
        chromium_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        # Intentar usar el binario de Chromium en Ubuntu
        try:
            chromium_options.binary_location = "/usr/bin/chromium-browser"  # Ubicación típica en Ubuntu
            logger.info(f"ℹ️ Usando Chromium desde {chromium_options.binary_location}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo encontrar Chromium en {chromium_options.binary_location}: {e}")
            logger.info("ℹ️ Continuando sin especificar binario...")
            chromium_options.binary_location = None
        
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chromium_options)

class OperaGXWebHandler(BaseWebHandler):
    browser_name = "OperaGX"
    process_names = ["operagx"]
    driver_names = ["operadriver"]

    def start(self):
        logger.info(f"🌐 Iniciando navegador OperaGX...")
        USER_DATA_DIR = self.get_profile_dir("operagx")
        self.profile_dir = USER_DATA_DIR
        logger.info(f"📂 Ruta de perfil de usuario: {USER_DATA_DIR}")
        opera_options = webdriver.ChromeOptions()
        opera_options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        opera_options.add_argument("--profile-directory=Profile 1")
        opera_options.add_argument("--no-sandbox")
        opera_options.add_argument("--disable-dev-shm-usage")
        opera_options.add_argument("--disable-gpu")
        opera_options.add_argument("--disable-logging")
        opera_options.add_argument("--disk-cache-size=524288000")
        opera_options.add_argument("--no-default-browser-check")
        opera_options.add_argument("--ignore-certificate-errors")
        opera_options.add_argument("--log-level=3")
        opera_options.add_argument("--enable-gpu-rasterization")
        opera_options.add_argument("--disable-background-networking")
        opera_options.add_argument("--media-cache-size=524288000")
        opera_options.add_argument("--disable-blink-features=AutomationControlled")
        opera_options.add_argument("--disable-features=SSLVersionFallback,SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure")
        opera_options.add_argument("--silent")
        opera_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        # Primero intentar sin especificar binario
        try:
            service = ChromeService(OperaDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=opera_options)
            logger.info("ℹ️  Iniciando OperaGX sin especificar binario...")
        except Exception as e:
            logger.warning(f"⚠️  No se pudo iniciar OperaGX: {e}")
            logger.info("ℹ️  Intentando con ruta de Ubuntu...")
            
            # Intentar con ruta de Ubuntu
            try:
                opera_options.binary_location = "/usr/bin/opera-gx"  # Ubicación típica en Ubuntu
                logger.info(f"ℹ️  Usando OperaGX desde {opera_options.binary_location}")
                service = ChromeService(OperaDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=opera_options)
            except Exception as e:
                logger.warning(f"⚠️  No se pudo encontrar OperaGX en {opera_options.binary_location}: {e}")
                logger.info("ℹ️  Continuando sin especificar binario...")
                opera_options.binary_location = None
                service = ChromeService(OperaDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=opera_options)

class EdgeWebHandler(BaseWebHandler):
    browser_name = "Edge"
    process_names = ["msedge"]
    driver_names = ["msedgedriver"]

    def start(self):
        logger.info(f"🌐 Iniciando navegador Edge...")
        # self.check_processes()
        # self.kill()
        USER_DATA_DIR = self.get_profile_dir("edge")
        self.profile_dir = USER_DATA_DIR
        logger.info(f"📂 Ruta de perfil de usuario: {USER_DATA_DIR}")
        edge_options = webdriver.EdgeOptions()
        edge_options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        edge_options.add_argument("--profile-directory=Profile 1")
        # edge_options.add_argument("--headless=new")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--disable-logging")
        edge_options.add_argument("--disk-cache-size=524288000")
        edge_options.add_argument("--no-default-browser-check")
        edge_options.add_argument("--ignore-certificate-errors")
        edge_options.add_argument("--log-level=3")
        edge_options.add_argument("--enable-gpu-rasterization")
        edge_options.add_argument("--disable-background-networking")
        edge_options.add_argument("--media-cache-size=524288000")
        edge_options.add_argument("--disable-blink-features=AutomationControlled")
        edge_options.add_argument("--disable-features=SSLVersionFallback,SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure")
        edge_options.add_argument("--silent")
        edge_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        # Primero intentar sin especificar binario
        try:
            service = EdgeService(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=edge_options)
            logger.info("ℹ️  Iniciando Edge sin especificar binario...")
        except Exception as e:
            logger.warning(f"⚠️  No se pudo iniciar Edge: {e}")
            logger.info("ℹ️  Intentando con ruta de Ubuntu...")
            
            # Intentar con ruta de Ubuntu
            try:
                edge_options.binary_location = "/usr/bin/microsoft-edge"  # Ubicación típica en Ubuntu
                logger.info(f"ℹ️  Usando Edge desde {edge_options.binary_location}")
                service = EdgeService(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=edge_options)
            except Exception as e:
                logger.warning(f"⚠️  No se pudo encontrar Edge en {edge_options.binary_location}: {e}")
                logger.info("ℹ️  Continuando sin especificar binario...")
                edge_options.binary_location = None
                service = EdgeService(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=edge_options)

