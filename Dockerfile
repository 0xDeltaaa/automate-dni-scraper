# Usar imagen base de Python con Chrome
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY requirements.txt .
COPY *.py .
COPY *.csv .
COPY *.md .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Configurar variables de entorno para Chrome
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome
ENV DISPLAY=:99

# Exponer puerto (opcional)
EXPOSE 8080

# Comando por defecto
CMD ["python", "procesar_csv.py", "--archivo", "automate.csv", "--delay", "1"]