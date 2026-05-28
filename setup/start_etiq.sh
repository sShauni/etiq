#!/bin/bash

# Inicia Xorg no LCD (fb1) na VT7, sem cursor
Xorg :0 vt7 -nocursor -nolisten tcp &
XORG_PID=$!

# Aguarda socket do X aparecer (máx 30s)
TIMEOUT=30
while [ $TIMEOUT -gt 0 ] && [ ! -e /tmp/.X11-unix/X0 ]; do
    sleep 1
    TIMEOUT=$((TIMEOUT - 1))
done

if [ ! -e /tmp/.X11-unix/X0 ]; then
    echo "Erro: Xorg nao iniciou em 30s" >&2
    kill $XORG_PID 2>/dev/null
    exit 1
fi

export DISPLAY=:0
cd /home/pi/etiq
python3 main.py

kill $XORG_PID 2>/dev/null
