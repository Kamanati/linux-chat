mkdir -p $HOME/bin/

echo "Setting up Bypasser....."

wget https://github.com/Kamanati/linux-chat/raw/refs/heads/main/bypass -O /data/data/com.termux/files/usr/bin/termux-url-opener
chmod +x /data/data/com.termux/files/usr/bin/termux-url-opener

if [ $? -eq 0 ];then
     echo "Succes..."
else
     echo "Failed..."
fi
