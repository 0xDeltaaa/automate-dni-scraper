#!/bin/bash
# Railway startup script

echo "🚀 Iniciando automatización DNI en Railway..."

# Instalar Chrome
apt-get update
apt-get install -y chromium-browser chromium-chromedriver
ln -sf /usr/bin/chromium-browser /usr/bin/google-chrome
ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver

# Instalar dependencias Python
pip install -r requirements.txt

# Ejecutar procesamiento
python procesar_csv.py --archivo automate.csv --delay 1