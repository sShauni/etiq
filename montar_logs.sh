#!/bin/bash

echo "[+] Verificando ponto de montagem..."

if mountpoint -q /mnt/logs; then
    echo "[✓] Já montado: /mnt/logs"
    exit 0
fi

echo "[>] Tentando montar..."
mount -t cifs //192.168.0.250/Compumate/ArquivosProducao /mnt/logs \
  -o credentials=/etc/samba_credencial,iocharset=utf8,file_mode=0777,dir_mode=0777,noperm

RET=$?
if [ $RET -ne 0 ]; then
    echo "[X] Erro ao montar. Código: $RET"
    exit $RET
else
    echo "[✓] Montado com sucesso!"
    exit 0
fi
