sudo apt-get update
sudo apt install python3 python3-tk cifs-utils
sudo apt-get install python3-openpyxl
sudo rm -rf LCD-show

sudo mkdir -p /mnt/logs
sudo mount -t cifs //192.168.0.250/Compumate/ArquivosProducao	-o username=API,passord=25565

git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show


echo "
Dependências instaladas..."
