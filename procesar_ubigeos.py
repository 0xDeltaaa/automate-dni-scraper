#!/usr/bin/env python3
"""
Procesador de Ubigeos - Solo Fase 2
Extrae ubigeos del portal del Congreso usando DNIs con códigos verificadores ya obtenidos
"""

import pandas as pd
import time
import logging
from congreso_scraper import CongresoScraper
import re
from pathlib import Path

def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ubigeos_procesamiento.log', encoding='utf-8'),
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

def procesar_ubigeos(archivo_csv, inicio_desde=0, cantidad_procesar=None, delay=3):
    """
    Procesar ubigeos desde CSV que ya tiene códigos verificadores
    
    Args:
        archivo_csv: Ruta al archivo CSV con códigos verificadores
        inicio_desde: Fila desde donde iniciar (0 = primera fila de datos)
        cantidad_procesar: Cantidad de DNIs a procesar (None = todos)
        delay: Segundos entre requests
    """
    logger = setup_logging()
    
    # Verificar que existe el archivo
    if not Path(archivo_csv).exists():
        logger.error(f"No se encuentra el archivo: {archivo_csv}")
        return False
    
    # Leer CSV preservando los ceros iniciales en DNIs
    logger.info(f"Leyendo archivo: {archivo_csv}")
    df = pd.read_csv(archivo_csv, dtype={'D N I': str})
    
    logger.info(f"Total de registros en CSV: {len(df)}")
    logger.info(f"Columnas: {list(df.columns)}")
    
    # Verificar que existen las columnas necesarias
    dni_column = None
    for col in df.columns:
        if 'DNI' in col.upper() or 'D N I' in col.upper():
            dni_column = col
            break
    
    if not dni_column:
        logger.error("No se encontró columna de DNI")
        return False
    
    if 'CODIGO_VERIFICADOR' not in df.columns:
        logger.error("No se encontró columna CODIGO_VERIFICADOR. Este archivo debe tener códigos verificadores.")
        return False
    
    logger.info(f"Columna DNI encontrada: {dni_column}")
    
    # Agregar columna de ubigeo si no existe
    if 'UBIGEO' not in df.columns:
        df['UBIGEO'] = ''
    
    # Filtrar solo registros con código verificador válido
    df_validos = df[
        (df['CODIGO_VERIFICADOR'].notna()) & 
        (df['CODIGO_VERIFICADOR'] != '') & 
        (df['CODIGO_VERIFICADOR'] != 'DNI_INVALIDO') & 
        (df['CODIGO_VERIFICADOR'] != 'NO_ENCONTRADO') &
        (df['CODIGO_VERIFICADOR'] != 'ERROR')
    ].copy()
    
    logger.info(f"Registros con código verificador válido: {len(df_validos)}")
    
    if len(df_validos) == 0:
        logger.error("No hay registros con códigos verificadores válidos para procesar")
        return False
    
    # Determinar rango a procesar
    total_validos = len(df_validos)
    fin = inicio_desde + cantidad_procesar if cantidad_procesar else total_validos
    fin = min(fin, total_validos)
    
    logger.info(f"Procesando desde registro {inicio_desde} hasta {fin-1} (total: {fin-inicio_desde} registros)")
    
    # Procesar cada DNI con scraper individual (más estable)
    try:
        procesados = 0
        exitosos = 0
        
        # Procesar cada registro válido en el rango especificado
        for i in range(inicio_desde, fin):
                row = df_validos.iloc[i]
                dni_raw = row[dni_column]
                codigo_verificador_raw = row['CODIGO_VERIFICADOR']
                
                # Limpiar código verificador (quitar decimales si es número)
                if pd.isna(codigo_verificador_raw):
                    codigo_verificador = ''
                else:
                    codigo_verificador = str(int(float(codigo_verificador_raw))) if str(codigo_verificador_raw).replace('.', '').isdigit() else str(codigo_verificador_raw).strip()
                
                dni_limpio = limpiar_dni(dni_raw)
                
                logger.info(f"Procesando registro {i+1}/{total_validos}: DNI {dni_raw} con código {codigo_verificador}")
                
                if not dni_limpio:
                    logger.warning(f"DNI inválido en registro {i+1}: {dni_raw}")
                    # Buscar el índice original en el DataFrame completo
                    idx_original = df[df[dni_column] == dni_raw].index[0]
                    df.at[idx_original, 'UBIGEO'] = 'DNI_INVALIDO'
                    procesados += 1
                    continue
                
                if not codigo_verificador or codigo_verificador in ['DNI_INVALIDO', 'NO_ENCONTRADO', 'ERROR']:
                    logger.warning(f"Código verificador inválido para DNI {dni_limpio}: {codigo_verificador}")
                    # Buscar el índice original en el DataFrame completo
                    idx_original = df[df[dni_column] == dni_raw].index[0]
                    df.at[idx_original, 'UBIGEO'] = 'SIN_CODIGO_VALIDO'
                    procesados += 1
                    continue
                
                try:
                    # Crear scraper individual para cada DNI (más estable)
                    with CongresoScraper(headless=True, delay=delay) as scraper:
                        ubigeo = scraper.get_ubigeo(dni_limpio, codigo_verificador)
                    
                    # Buscar el índice original en el DataFrame completo
                    idx_original = df[df[dni_column] == dni_raw].index[0]
                    
                    if ubigeo:
                        df.at[idx_original, 'UBIGEO'] = ubigeo
                        logger.info(f"[OK] DNI {dni_limpio} -> Ubigeo: {ubigeo}")
                        exitosos += 1
                    else:
                        df.at[idx_original, 'UBIGEO'] = 'NO_ENCONTRADO'
                        logger.warning(f"[ERROR] No se encontró ubigeo para DNI: {dni_limpio}")
                    
                    procesados += 1
                    
                    # Guardar progreso cada 5 registros
                    if procesados % 5 == 0:
                        nombre_temporal = f"ubigeos_progreso_{procesados}.csv"
                        df.to_csv(nombre_temporal, index=False)
                        logger.info(f"Progreso guardado en: {nombre_temporal}")
                    
                    # Pausa entre requests
                    if i < fin - 1:  # No hacer pausa en el último
                        logger.info(f"Esperando {delay} segundos...")
                        time.sleep(delay)
                
                except Exception as e:
                    logger.error(f"Error procesando DNI {dni_limpio}: {e}")
                    # Buscar el índice original en el DataFrame completo
                    idx_original = df[df[dni_column] == dni_raw].index[0]
                    df.at[idx_original, 'UBIGEO'] = 'ERROR'
                    procesados += 1
    
    except Exception as e:
        logger.error(f"Error con el scraper del Congreso: {e}")
        return False
    
    # Guardar CSV final
    nombre_final = f"ubigeos_completo_{inicio_desde}_{fin}.csv"
    df.to_csv(nombre_final, index=False)
    
    # Mostrar resumen
    print(f"\n{'='*60}")
    print(f"RESUMEN DEL PROCESAMIENTO DE UBIGEOS")
    print(f"{'='*60}")
    print(f"Total registros procesados: {procesados}")
    print(f"Ubigeos obtenidos exitosamente: {exitosos}")
    print(f"Errores/No encontrados: {procesados - exitosos}")
    print(f"Tasa de éxito: {(exitosos/max(procesados,1)*100):.1f}%")
    print(f"Archivo final guardado: {nombre_final}")
    print(f"{'='*60}")
    
    return nombre_final

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Procesador de Ubigeos desde CSV con códigos verificadores')
    parser.add_argument('--archivo', '-a', default='automate_con_codigos_0_50.csv', help='Archivo CSV con códigos verificadores')
    parser.add_argument('--inicio', '-i', type=int, default=0, help='Registro desde donde iniciar (0 = primero)')
    parser.add_argument('--cantidad', '-c', type=int, help='Cantidad de registros a procesar')
    parser.add_argument('--delay', '-d', type=int, default=3, help='Segundos entre requests')
    
    args = parser.parse_args()
    
    print("🌍 Iniciando procesamiento de UBIGEOS...")
    print(f"Archivo: {args.archivo}")
    print(f"Inicio desde registro: {args.inicio}")
    print(f"Cantidad a procesar: {args.cantidad or 'Todos los válidos'}")
    print(f"Delay entre requests: {args.delay} segundos")
    print("-" * 60)
    
    resultado = procesar_ubigeos(
        archivo_csv=args.archivo,
        inicio_desde=args.inicio,
        cantidad_procesar=args.cantidad,
        delay=args.delay
    )
    
    if resultado:
        print(f"\n✅ Procesamiento completado exitosamente: {resultado}")
    else:
        print(f"\n❌ Error en el procesamiento")

if __name__ == "__main__":
    main()