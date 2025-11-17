sudo install cups -y
sudo usermod -aG lpadmin $USER
sudo systemctl enable cups
sudo systemctl start cups
echo ""
lpinfo -v
echo ""
lpinfo -m | grep zebra
echo ""
echo "use lpadmin -p Thermal -E -v [uri] -m raw"

