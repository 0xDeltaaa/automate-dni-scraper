# Automatizador DNI → Código Verificador → Ubigeo

Sistema automatizado para obtener información completa de DNIs peruanos en **2 FASES**:

## 🔄 **PROCESO EN DOS FASES (RECOMENDADO)**

### **FASE 1**: Obtener códigos verificadores
```bash
python procesar_csv.py --archivo automate.csv --delay 1
```
- **Entrada**: `automate.csv` (DNIs originales)  
- **Salida**: `automate_con_codigos_0_XXXX.csv` (con códigos verificadores)
- **Tiempo**: ~8 segundos por DNI

### **FASE 2**: Obtener ubigeos usando los códigos
```bash
python procesar_ubigeos.py --archivo automate_con_codigos_0_XXXX.csv --delay 3
```
- **Entrada**: Archivo con códigos verificadores de la Fase 1
- **Salida**: `ubigeos_completo_0_XXXX.csv` (con ubigeos)
- **Tiempo**: ~12 segundos por DNI

## 📁 **Archivos del core**

- `procesar_csv.py`: **Fase 1** - Obtiene códigos verificadores de elDNI.com
- `procesar_ubigeos.py`: **Fase 2** - Obtiene ubigeos del portal del Congreso  
- `dni_scraper.py`: Scraper para elDNI.com
- `congreso_scraper.py`: Scraper para portal del Congreso
- `automate.csv`: Tu archivo de datos original (3000 DNIs)
- `automate_con_codigos_0_50.csv`: Ejemplo con 50 DNIs procesados

## Instalación

1. Instalar Google Chrome desde: https://www.google.com/chrome/
2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## 🚀 **Uso recomendado**

### Para procesar toda tu base de datos:

```bash
# FASE 1: Obtener todos los códigos verificadores
python procesar_csv.py --archivo automate.csv --delay 1

# FASE 2: Obtener todos los ubigeos  
python procesar_ubigeos.py --archivo automate_con_codigos_0_3000.csv --delay 3
```

### Para pruebas pequeñas:

```bash
# FASE 1: Solo 10 DNIs
python procesar_csv.py --archivo automate.csv --cantidad 10 --delay 1

# FASE 2: Usar el resultado de la fase 1
python procesar_ubigeos.py --archivo automate_con_codigos_0_10.csv --delay 3
```

## Parámetros

- `--archivo` o `-a`: Archivo CSV de entrada (default: automate.csv)
- `--inicio` o `-i`: Fila desde donde iniciar (default: 0)
- `--cantidad` o `-c`: Cantidad de registros a procesar (default: todos)
- `--delay` o `-d`: Segundos entre requests (default: 3)

## ✅ **Resultados**

El procesamiento genera archivos CSV con:
- ✅ Todas las columnas originales
- ✅ `CODIGO_VERIFICADOR`: Código verificador del DNI (Fase 1)
- ✅ `UBIGEO`: Ubicación geográfica completa (Fase 2)
- ✅ Guardado automático de progreso

## 🎯 **Características**

- 🔄 **Solo Chrome**: Navegador único, sin Edge
- 🛡️ **Driver individual**: Un navegador por cada DNI (máxima estabilidad)
- 💾 **Guardado de progreso**: Cada 10 registros (Fase 1) o 5 (Fase 2)
- 🚫 **Sin detección**: Navegación humana simulada
- ⚡ **Proceso separado**: Mayor control y estabilidad

## ⏱️ **Tiempo estimado para 3000 DNIs**

- **Fase 1**: ~6-8 horas (solo códigos)
- **Fase 2**: ~8-10 horas (usando códigos obtenidos)
- **Total**: ~14-18 horas completas

## 🎉 **Tasa de éxito**

- **Fase 1**: >95% (códigos verificadores)
- **Fase 2**: 100% (ubigeos con códigos válidos)

## Notas importantes

- Instalar Google Chrome antes de usar
- Los DNIs deben tener exactamente 8 dígitos
- Se recomienda usar delay de 2-3 segundos para evitar bloqueos
- Los resultados se guardan automáticamente