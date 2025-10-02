#!/bin/bash
# Script para ejecutar el procesamiento de DNIs en GitHub Codespaces
# con máxima seguridad y persistencia

echo "🚀 INICIANDO PROCESAMIENTO DE DNIs EN CODESPACES"
echo "=================================================="

# Crear sesión tmux persistente
echo "📡 Creando sesión tmux persistente..."
tmux new-session -d -s dni_processing

# Ejecutar el procesamiento dentro de tmux
echo "⚡ Iniciando procesamiento de códigos verificadores..."
tmux send-keys -t dni_processing "python procesar_csv.py --archivo automate.csv --delay 1" Enter

echo "✅ PROCESO INICIADO EXITOSAMENTE"
echo "================================="
echo ""
echo "📋 COMANDOS ÚTILES:"
echo "• Ver progreso:     tmux attach -t dni_processing"
echo "• Salir de tmux:    Ctrl+B, luego D"
echo "• Listar archivos:  ls -la automate_progreso_*.csv"
echo "• Ver logs:         tail -f dni_procesamiento.log"
echo ""
echo "🔥 El proceso corre independiente del navegador!"
echo "💪 Puedes cerrar el navegador sin problema"
echo ""
echo "⏰ Tiempo estimado: 5-6 horas para 3000 DNIs"
echo "💾 Respaldo automático cada 100 DNIs"