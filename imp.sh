sudo install cups -y
sudo usermod -aG lpadmin $USER
sudo systemctl enable cups
sudo systemctl start cups
lpinfo -v

echo "use lpadmin -p Thermal -E -v [uri] -m [ppd]"
echo "ppd: lpadmin -m | grep [nome do fabricante. ex. zebra]"
