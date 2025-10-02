from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from typing import Optional, Tuple
import re

class DNIScraper:
    """Web scraper para obtener códigos verificadores de DNI desde elDNI.com"""
    
    def __init__(self, headless: bool = True, delay: int = 1):
        self.url = "https://eldni.com/pe/obtener-digito-verificador-del-dni"
        self.delay = delay
        self.setup_logging()
        self.driver = self.setup_driver(headless)
    
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self, headless: bool):
        """Configurar el driver web (Chrome o Edge)"""
        driver = None
        
        # Configurar solo Chrome
        try:
            self.logger.info("Configurando Chrome...")
        
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless")
            
            # Opciones adicionales para evitar detección
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent para parecer más humano
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Ejecutar script para ocultar webdriver
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Driver de Chrome configurado correctamente")
            return driver
            
        except Exception as e:
            self.logger.error(f"Error configurando Chrome: {e}")
            raise Exception("No se pudo configurar Chrome. Asegúrate de tener Google Chrome instalado.")
    
    def validate_dni(self, dni: str) -> bool:
        """Validar formato de DNI peruano (8 dígitos)"""
        dni = dni.strip()
        return bool(re.match(r'^\d{8}$', dni))
    
    def get_codigo_verificador(self, dni: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Obtener código verificador de un DNI
        Retorna: (codigo_verificador, departamento, provincia)
        """
        if not self.validate_dni(dni):
            self.logger.error(f"DNI inválido: {dni}")
            return None, None, None
        
        try:
            self.logger.info(f"Procesando DNI: {dni}")
            
            # Navegar a la página
            self.driver.get(self.url)
            time.sleep(self.delay)
            
            # Buscar el campo de entrada del DNI (usar xpath más genérico)
            dni_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
            )
            
            # Limpiar y escribir el DNI
            dni_input.clear()
            dni_input.send_keys(dni)
            time.sleep(1)
            
            # Buscar y hacer clic en el botón de consulta
            consultar_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='btn-buscar-por-dniveri']"))
            )
            consultar_btn.click()
            
            # Esperar a que aparezca el resultado
            time.sleep(self.delay + 2)
            
            # Obtener el código verificador usando el selector específico
            codigo_verificador_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='digito_verificador']"))
            )
            
            # Intentar obtener el valor del elemento
            codigo_verificador = codigo_verificador_element.get_attribute("value")
            if not codigo_verificador:
                codigo_verificador = codigo_verificador_element.text.strip()
            
            self.logger.info(f"Código encontrado: {codigo_verificador}")
            
            # Intentar obtener información adicional (departamento, provincia)
            departamento = None
            provincia = None
            
            try:
                # Buscar elementos que puedan contener departamento y provincia
                info_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'result') or contains(@class, 'info')]//text()")
                
                for element in info_elements:
                    text = element.text.lower()
                    if 'departamento' in text or 'región' in text:
                        departamento = element.text.split(':')[-1].strip()
                    elif 'provincia' in text:
                        provincia = element.text.split(':')[-1].strip()
                        
            except Exception as e:
                self.logger.warning(f"No se pudo obtener información adicional para DNI {dni}: {e}")
            
            if codigo_verificador:
                self.logger.info(f"DNI {dni} - Código verificador: {codigo_verificador}")
                return codigo_verificador, departamento, provincia
            else:
                # Hacer screenshot para depuración
                screenshot_path = f"debug_dni_{dni}.png"
                self.driver.save_screenshot(screenshot_path)
                self.logger.warning(f"No se encontró código verificador para DNI: {dni}. Screenshot guardado: {screenshot_path}")
                
                # Obtener HTML para depuración
                try:
                    page_source = self.driver.page_source
                    with open(f"debug_html_{dni}.html", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    self.logger.debug(f"HTML guardado: debug_html_{dni}.html")
                except:
                    pass
                
                return None, None, None
                
        except Exception as e:
            self.logger.error(f"Error procesando DNI {dni}: {e}")
            return None, None, None
    
    def process_multiple_dnis(self, dnis: list) -> dict:
        """
        Procesar múltiples DNIs
        Retorna diccionario con resultados
        """
        results = {}
        total = len(dnis)
        
        for i, dni in enumerate(dnis, 1):
            self.logger.info(f"Procesando {i}/{total}: {dni}")
            
            codigo, departamento, provincia = self.get_codigo_verificador(dni)
            
            results[dni] = {
                'codigo_verificador': codigo,
                'departamento': departamento,
                'provincia': provincia,
                'success': codigo is not None
            }
            
            # Pausa entre requests para evitar ser bloqueado
            if i < total:
                time.sleep(self.delay)
        
        return results
    
    def close(self):
        """Cerrar el driver"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Driver cerrado")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()