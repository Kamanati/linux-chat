mkdir -p $HOME/bin/

echo "Setting up Bypasser....."

wget https://github.com/Kamanati/linux-chat/raw/refs/heads/main/bypass -O $HOME/bin/termux-url-opener
chmod +x $HOME/bin/termux-url-opener

if [ $? -eq 0 ];then
     echo "Succes..."
else
     echo "Failed..."
fi