#!/bin/bash
# Cerrar el servidor ContHome
PID_FILE="/Users/branel/Documents/ContHome/.server.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo ""
    echo "  ContHome cerrado correctamente."
    echo ""
else
    echo ""
    echo "  ContHome no esta corriendo."
    echo ""
fi
sleep 2
