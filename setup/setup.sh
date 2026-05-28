#!/bin/bash
set -e

SETUP_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=================================================="
echo "  Setup Sistema de Etiquetas"
echo "  Raspberry Pi Zero 2W + Raspbian Lite + LCD 3.5\""
echo "=================================================="

# 1. Pacotes
echo ""
echo "[1/7] Instalando pacotes..."
sudo apt-get update -q
sudo apt-get install -y \
    git \
    python3 python3-tk python3-xlib python3-openpyxl \
    cifs-utils \
    xserver-xorg-core \
    xserver-xorg-input-all \
    xserver-xorg-video-fbdev \
    xinit

# 2. Grupos necessários para X server e framebuffer
echo ""
echo "[2/7] Configurando grupos do usuário pi..."
sudo usermod -aG tty,video,input,render pi 2>/dev/null || true

# 3. Credencial Samba e ponto de montagem
echo ""
echo "[3/7] Configurando Samba..."
sudo cp "$SETUP_DIR/samba_credencial" /etc/samba_credencial
sudo chmod 600 /etc/samba_credencial
sudo mkdir -p /mnt/logs
sudo chmod +x /home/pi/etiq/montar_logs.sh 2>/dev/null || true

# 4. Serviço de montagem de logs via SMB
echo ""
echo "[4/7] Habilitando serviço de logs..."
sudo cp "$SETUP_DIR/montar-logs.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable montar-logs.service

# 5. Xorg para LCD 3.5" (fb1) + touch via evdev
echo ""
echo "[5/7] Configurando Xorg para LCD 3.5\"..."
sudo mkdir -p /etc/X11/xorg.conf.d
sudo cp "$SETUP_DIR/99-lcd.conf" /etc/X11/xorg.conf.d/
sudo cp "$SETUP_DIR/40-touch.conf" /etc/X11/xorg.conf.d/

# 6. Serviço de startup — inicia Xorg + app direto, sem depender de login
echo ""
echo "[6/7] Configurando serviço de startup..."
cp "$SETUP_DIR/start_etiq.sh" /home/pi/etiq/start_etiq.sh
chmod +x /home/pi/etiq/start_etiq.sh
sudo cp "$SETUP_DIR/startup.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable startup.service
# Remove override de autologin se existir (não é mais necessário)
sudo rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
sudo systemctl daemon-reload

# 7. Driver do LCD 3.5" — reinicia o Pi ao concluir
echo ""
echo "[7/7] Instalando driver do LCD 3.5\" (o Pi vai reiniciar)..."
if [ ! -d "$SETUP_DIR/LCD-show" ]; then
    git clone https://github.com/goodtft/LCD-show.git "$SETUP_DIR/LCD-show"
fi
chmod -R 755 "$SETUP_DIR/LCD-show"
cd "$SETUP_DIR/LCD-show" && sudo ./LCD35-show
# LCD35-show reinicia o Pi automaticamente — nada abaixo desta linha é executado
