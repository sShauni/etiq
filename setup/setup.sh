sudo apt-get update
sudo apt install python3 python3-tk python3-xlib cifs-utils -y
sudo apt-get install python3-openpyxl -y

# X server mínimo para rodar Tkinter no Raspbian Lite
sudo apt install --no-install-recommends \
    xserver-xorg-core \
    xserver-xorg-video-fbdev \
    xinit -y

# Adiciona pi aos grupos necessários para o X server
sudo usermod -aG tty,video,input,render pi

# Serviço de logs de produção
sudo mv montar-logs.service /etc/systemd/system/
sudo systemctl enable montar-logs.service
sudo systemctl start montar-logs.service

# Credencial Samba
sudo mv samba_credencial /etc/

# LCD: configura X para usar o framebuffer do display (fb1)
sudo mkdir -p /etc/X11/xorg.conf.d
sudo mv 99-lcd.conf /etc/X11/xorg.conf.d/

# Auto-login no tty1 como usuário pi
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo mv autologin.conf /etc/systemd/system/getty@tty1.service.d/

# Inicia X e a aplicação automaticamente ao logar no tty1
cp bash_profile /home/pi/.bash_profile

# Script de lançamento da aplicação via startx
cp start_etiq.sh /home/pi/etiq/start_etiq.sh
chmod +x /home/pi/etiq/start_etiq.sh

sudo mkdir -p /mnt/logs
sudo mount -t cifs //192.168.0.250/Compumate/Producao -o username=compumate,password=TAGCompumate2025*

# Instala driver do LCD 3.5"
sudo rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show && sudo ./LCD35-show

echo "
Dependências instaladas..."
