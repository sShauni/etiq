sudo apt-get update
sudo apt install python3 python3-tk cifs-utils -y
sudo apt-get install python3-openpyxl -y
sudo rm -rf LCD-show

sudo mv montar-logs.service /etc/systemd/system/
sudo mv startup.service /etc/systemd/system/
sudo mv samba_credencial /etc/

sudo systemctl enable montar-logs.service
sudo systemctl enable startup.service
sudo systemctl start montar-logs.service
sudo systemctl start startup.service

sudo mkdir -p /mnt/logs
sudo mount -t cifs //192.168.0.250/Compumate/Producao	-o username=compumate,passord=TAGCompumate2025*

git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show

sudo cp logo.png /usr/share/plymouth/themes/pix/splash.png
pcmanfm --set-wallpaper="" --wallpaper-mode=color

echo "
Dependências instaladas..."
