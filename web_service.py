#!/usr/bin/env python3
"""
Web service wrapper para el procesador de DNIs
"""
from flask import Flask, jsonify, request
import threading
import subprocess
import os
import glob
import time

app = Flask(__name__)
process_thread = None
process_status = {"status": "idle", "processed": 0, "total": 3000, "current_dni": None, "errors": 0}

def run_processing():
    """Ejecutar el procesamiento en background"""
    global process_status
    process_status["status"] = "running"
    process_status["start_time"] = time.time()
    
    try:
        # Ejecutar el procesamiento
        process = subprocess.Popen(
            ["python", "procesar_csv.py", "--archivo", "automate.csv", "--delay", "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Leer output en tiempo real
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"PROCESSING: {line.strip()}")
                # Extraer información del procesamiento
                if "Procesando fila" in line:
                    try:
                        parts = line.split(":")
                        if len(parts) > 1:
                            fila_info = parts[1].strip().split("/")
                            if len(fila_info) >= 2:
                                process_status["processed"] = int(fila_info[0])
                                process_status["total"] = int(fila_info[1].split()[0])
                    except:
                        pass
                elif "Procesando DNI:" in line:
                    try:
                        dni = line.split("Procesando DNI:")[-1].strip()
                        process_status["current_dni"] = dni
                    except:
                        pass
                elif "ERROR" in line or "WARNING" in line:
                    process_status["errors"] += 1
        
        process.wait()
        
        if process.returncode == 0:
            process_status["status"] = "completed"
        else:
            process_status["status"] = "error"
            
    except Exception as e:
        process_status["status"] = "error"
        process_status["error"] = str(e)
        print(f"ERROR: {e}")

@app.route('/')
def home():
    """Página principal con estado del procesamiento"""
    return jsonify({
        "service": "DNI Automation Service",
        "status": process_status["status"],
        "processed": process_status["processed"],
        "total": process_status["total"],
        "current_dni": process_status.get("current_dni"),
        "errors": process_status["errors"],
        "progress_percentage": round((process_status["processed"] / process_status["total"]) * 100, 2),
        "uptime": time.time() - process_status.get("start_time", time.time())
    })

@app.route('/start')
def start_processing():
    """Iniciar el procesamiento"""
    global process_thread
    
    if process_status["status"] == "running":
        return jsonify({"error": "Processing already running"}), 400
    
    process_thread = threading.Thread(target=run_processing)
    process_thread.daemon = True
    process_thread.start()
    
    return jsonify({"message": "Processing started", "status": "running"})

@app.route('/status')
def get_status():
    """Obtener estado del procesamiento"""
    # Buscar archivos de progreso
    progress_files = glob.glob("automate_progreso_*.csv")
    latest_progress = 0
    if progress_files:
        latest_file = max(progress_files, key=os.path.getctime)
        latest_progress = int(latest_file.split('_')[-1].split('.')[0])
    
    return jsonify({
        "status": process_status["status"],
        "processed": max(process_status["processed"], latest_progress),
        "total": process_status["total"],
        "current_dni": process_status.get("current_dni"),
        "errors": process_status["errors"],
        "progress_files": len(progress_files),
        "latest_progress_file": latest_file if progress_files else None
    })

@app.route('/health')
def health_check():
    """Health check para Cloud Run"""
    return jsonify({"status": "healthy", "service": "dni-automation"})

if __name__ == '__main__':
    # Auto-iniciar el procesamiento
    print("🚀 Iniciando servicio de automatización DNI...")
    start_processing()
    
    # Ejecutar Flask
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)