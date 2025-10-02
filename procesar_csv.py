#!/usr/bin/env python3
"""
Procesador de códigos verificadores de DNI - Versión CSV
Lee un CSV, obtiene códigos verificadores y guarda en nuevo CSV con columna adicional
"""

import pandas as pd
import time
import logging
from dni_scraper import DNIScraper
import re
from pathlib import Path

def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('dni_procesamiento.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def limpiar_dni(dni_str):
    """Limpiar y validar DNI preservando ceros iniciales"""
    if pd.isna(dni_str) or dni_str == '' or dni_str == 'nan':
        return None
    
    # Convertir a string y limpiar espacios
    dni = str(dni_str).strip()
    
    # Eliminar caracteres no numéricos pero preservar estructura
    dni = re.sub(r'[^0-9]', '', dni)
    
    # Si tiene menos de 8 dígitos, completar con ceros a la izquierda
    if len(dni) < 8 and len(dni) > 0:
        dni = dni.zfill(8)
    
    # Validar que tenga exactamente 8 dígitos
    if len(dni) == 8 and dni.isdigit():
        return dni
    
    return None

def procesar_csv_dnis(archivo_csv, inicio_desde=0, cantidad_procesar=None, delay=3):
    """
    Procesar DNIs desde CSV y crear nuevo CSV con códigos verificadores
    
    Args:
        archivo_csv: Ruta al archivo CSV original
        inicio_desde: Fila desde donde iniciar (0 = primera fila de datos)
        cantidad_procesar: Cantidad de DNIs a procesar (None = todos)
        delay: Segundos entre requests
    """
    logger = setup_logging()
    
    # Verificar que existe el archivo
    if not Path(archivo_csv).exists():
        logger.error(f"No se encuentra el archivo: {archivo_csv}")
        return
    
    # Leer CSV original preservando los ceros iniciales en DNIs
    logger.info(f"Leyendo archivo: {archivo_csv}")
    df = pd.read_csv(archivo_csv, dtype={'D N I': str})
    
    logger.info(f"Total de registros en CSV: {len(df)}")
    logger.info(f"Columnas: {list(df.columns)}")
    
    # Encontrar columna de DNI
    dni_column = None
    for col in df.columns:
        if 'DNI' in col.upper() or 'D N I' in col.upper():
            dni_column = col
            break
    
    if not dni_column:
        logger.error("No se encontró columna de DNI")
        return
    
    logger.info(f"Columna DNI encontrada: {dni_column}")
    
    # Agregar columna para código verificador si no existe
    if 'CODIGO_VERIFICADOR' not in df.columns:
        df['CODIGO_VERIFICADOR'] = ''
    
    # Determinar rango a procesar
    total_filas = len(df)
    fin = inicio_desde + cantidad_procesar if cantidad_procesar else total_filas
    fin = min(fin, total_filas)
    
    logger.info(f"Procesando desde fila {inicio_desde} hasta {fin-1} (total: {fin-inicio_desde} registros)")
    
    # Inicializar scraper
    try:
        with DNIScraper(headless=True, delay=delay) as scraper:
            procesados = 0
            exitosos = 0
            
            # Procesar cada fila en el rango especificado
            for i in range(inicio_desde, fin):
                fila_actual = i + 1  # +1 porque el CSV tiene header
                dni_raw = df.iloc[i][dni_column]
                dni_limpio = limpiar_dni(dni_raw)
                
                logger.info(f"Procesando fila {fila_actual}/{total_filas}: {dni_raw}")
                
                if not dni_limpio:
                    logger.warning(f"DNI inválido en fila {fila_actual}: {dni_raw}")
                    df.at[i, 'CODIGO_VERIFICADOR'] = 'DNI_INVALIDO'
                    procesados += 1
                    continue
                
                try:
                    # Obtener código verificador
                    codigo, _, _ = scraper.get_codigo_verificador(dni_limpio)
                    
                    if codigo:
                        df.at[i, 'CODIGO_VERIFICADOR'] = codigo
                        logger.info(f"[OK] DNI {dni_limpio} -> Código: {codigo}")
                        exitosos += 1
                    else:
                        df.at[i, 'CODIGO_VERIFICADOR'] = 'NO_ENCONTRADO'
                        logger.warning(f"[ERROR] No se encontró código para DNI: {dni_limpio}")
                    
                    procesados += 1
                    
                    # Guardar progreso cada 100 registros
                    if procesados % 100 == 0:
                        nombre_temporal = f"automate_progreso_{procesados}.csv"
                        df.to_csv(nombre_temporal, index=False)
                        logger.info(f"Progreso guardado en: {nombre_temporal}")
                    
                    # Pausa entre requests
                    if i < fin - 1:  # No hacer pausa en el último
                        logger.info(f"Esperando {delay} segundos...")
                        time.sleep(delay)
                
                except Exception as e:
                    logger.error(f"Error procesando DNI {dni_limpio}: {e}")
                    df.at[i, 'CODIGO_VERIFICADOR'] = 'ERROR'
                    procesados += 1
    
    except Exception as e:
        logger.error(f"Error con el scraper: {e}")
        return
    
    # Guardar CSV final
    nombre_final = f"automate_con_codigos_{inicio_desde}_{fin}.csv"
    df.to_csv(nombre_final, index=False)
    
    # Mostrar resumen
    print(f"\n{'='*50}")
    print(f"RESUMEN DEL PROCESAMIENTO")
    print(f"{'='*50}")
    print(f"Total registros procesados: {procesados}")
    print(f"Códigos obtenidos exitosamente: {exitosos}")
    print(f"Errores/No encontrados: {procesados - exitosos}")
    print(f"Archivo final guardado: {nombre_final}")
    print(f"{'='*50}")
    
    return nombre_final

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Procesar códigos verificadores de DNI desde CSV')
    parser.add_argument('--archivo', '-a', default='automate.csv', help='Archivo CSV de entrada')
    parser.add_argument('--inicio', '-i', type=int, default=0, help='Fila desde donde iniciar (0 = primera)')
    parser.add_argument('--cantidad', '-c', type=int, help='Cantidad de registros a procesar')
    parser.add_argument('--delay', '-d', type=int, default=1, help='Segundos entre requests')
    
    args = parser.parse_args()
    
    print("Iniciando procesamiento de DNIs desde CSV...")
    print(f"Archivo: {args.archivo}")
    print(f"Inicio desde fila: {args.inicio}")
    print(f"Cantidad a procesar: {args.cantidad or 'Todos'}")
    print(f"Delay entre requests: {args.delay} segundos")
    print("-" * 50)
    
    procesar_csv_dnis(
        archivo_csv=args.archivo,
        inicio_desde=args.inicio,
        cantidad_procesar=args.cantidad,
        delay=args.delay
    )

if __name__ == "__main__":
    main()