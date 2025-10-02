#!/usr/bin/env python3
"""
Scraper para obtener ubigeo desde el portal del Congreso
https://wb2server.congreso.gob.pe/mpv/#/registro
"""

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

class CongresoScraper:
    """Web scraper para obtener ubigeo desde el portal del Congreso"""
    
    def __init__(self, headless: bool = True, delay: int = 2):
        self.url = "https://wb2server.congreso.gob.pe/mpv/#/registro"
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
    
    def setup_driver(self, headless: bool = True):
        """Configurar WebDriver solo con Chrome"""
        return self._setup_chrome_driver(headless)
    

    
    def _setup_chrome_driver(self, headless: bool):
        """Configurar Chrome WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        # Opciones para evitar detección
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
    
    def get_ubigeo(self, dni: str, codigo_verificador: str) -> Optional[str]:
        """
        Obtener ubigeo desde el portal del Congreso
        
        Args:
            dni: Número de DNI (8 dígitos)
            codigo_verificador: Código verificador del DNI
            
        Returns:
            String con el ubigeo o None si hay error
        """
        try:
            self.logger.info(f"Procesando DNI: {dni} con código: {codigo_verificador}")
            
            # REINICIAR COMPLETAMENTE PARA CADA REQUEST
            self.driver.delete_all_cookies()
            
            # Navegar a la página limpia
            self.driver.get(self.url)
            time.sleep(self.delay * 2)
            
            # Esperar a que cargue completamente
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Esperar a que aparezcan los elementos principales
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//p-dropdown[@id='tipoDocumento']"))
            )
            time.sleep(2)
            
            # 1. Localizar y hacer clic en el dropdown
            dropdown = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/app-register-form/div/section/form/div/div/div[2]/div/div/div/p-fieldset[1]/fieldset/div/div/div[1]/div[2]/div/p-dropdown/div/span"))
            )
            
            # Hacer scroll al elemento y click
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", dropdown)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", dropdown)
            time.sleep(2)
            
            # 2. Seleccionar "Documento Nacional de Identidad"
            dni_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/app-register-form/div/section/form/div/div/div[2]/div/div/div/p-fieldset[1]/fieldset/div/div/div[1]/div[2]/div/p-dropdown/div/div[3]/div/ul/p-dropdownitem[1]/li/span"))
            )
            self.driver.execute_script("arguments[0].click();", dni_option)
            time.sleep(2)
            
            # 3. Ingresar número de documento (DNI)
            doc_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='tmp_nrodocumento']"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", doc_input)
            self.driver.execute_script("arguments[0].value = '';", doc_input)  # Limpiar con JS
            doc_input.click()
            doc_input.send_keys(dni)
            time.sleep(1)
            
            # 4. Ingresar código verificador
            verificador_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='tmp_verificador']"))
            )
            self.driver.execute_script("arguments[0].value = '';", verificador_input)  # Limpiar con JS
            verificador_input.click()
            verificador_input.send_keys(codigo_verificador)
            time.sleep(1)
            
            # 5. Hacer clic en el botón "Validar"
            validar_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/app-register-form/div/section/form/div/div/div[2]/div/div/div/p-fieldset[1]/fieldset/div/div/div[2]/div[3]/div[1]/button"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", validar_btn)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", validar_btn)
            
            # 6. Esperar y obtener el ubigeo
            time.sleep(self.delay * 3)  # Más tiempo para procesar
            
            # Intentar múltiples formas de obtener el ubigeo
            ubigeo = None
            selectors_ubigeo = [
                "//*[@id='ubigeo']",
                "//input[@id='ubigeo']",
                "//input[contains(@placeholder, 'ubigeo')]"
            ]
            
            for selector in selectors_ubigeo:
                try:
                    ubigeo_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    
                    ubigeo = ubigeo_field.get_attribute("value")
                    if not ubigeo:
                        ubigeo = ubigeo_field.text.strip()
                    
                    if ubigeo:
                        break
                except:
                    continue
            
            if ubigeo:
                self.logger.info(f"Ubigeo encontrado para DNI {dni}: {ubigeo}")
                return ubigeo
            else:
                self.logger.warning(f"No se encontró ubigeo para DNI {dni}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error procesando DNI {dni}: {e}")
            
            # Hacer screenshot para depuración
            try:
                screenshot_path = f"debug_congreso_{dni}.png"
                self.driver.save_screenshot(screenshot_path)
                self.logger.debug(f"Screenshot guardado: {screenshot_path}")
            except:
                pass
                
            return None
    
    def close(self):
        """Cerrar el driver"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Driver cerrado")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def test_congreso_scraper():
    """Función de prueba"""
    # Datos de prueba (usar datos reales que tengas)
    dni_prueba = "73515183"
    codigo_prueba = "1"
    
    with CongresoScraper(headless=False, delay=2) as scraper:
        ubigeo = scraper.get_ubigeo(dni_prueba, codigo_prueba)
        print(f"DNI: {dni_prueba}")
        print(f"Código: {codigo_prueba}")
        print(f"Ubigeo: {ubigeo}")

if __name__ == "__main__":
    test_congreso_scraper()