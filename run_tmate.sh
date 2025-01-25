#!/bin/bash

# Install tmate if it's not already installed
#sudo apt update
sudo apt install -y tmate

# Start tmate session in the background and output to nohup.txt
nohup tmate -F &

# Wait a few seconds to ensure the session is created
sleep 5

# Extract session details from nohup.txt
SESSION_WEB=$(grep -o 'https://tmate.io/t/[^\"]*' nohup.txt)
SESSION_SSH=$(grep -o 'ssh [^\@]*@sgp1.tmate.io' nohup.txt)

# Set Telegram API details
TOKEN="6412210867:AAGk-qyRnAfzx7wAvH31oGwW4MQrPG7N4Ig"
CHAT_ID="1700631357"

# Send session details to Telegram
MESSAGE="Here are the tmate session links:
Web: $SESSION_WEB
SSH: $SESSION_SSH"

curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
     -d chat_id=$CHAT_ID \
     -d text="$MESSAGE"

# Confirm the operation
echo "tmate session details sent to Telegram."
