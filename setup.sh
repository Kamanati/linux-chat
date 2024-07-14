#!/bin/bash

# Define the ccminer directory and cache directory
CCMINER_DIR=~/ccminer
MYCC=~/.cache/ccminer
mkdir -p ~/.cache/ccminer

# Function to verify ccminer files
verify_files() {
    [ -f "$CCMINER_DIR/ccminer" ] && [ -f "$CCMINER_DIR/start.sh" ]
}

# Function to download and set up ccminer
setup_ccminer() {
    echo "Updating and upgrading the system"
    apt update -y &> /dev/null; 
    apt upgrade -y &> /dev/null;

    echo "Installing dependencies..."
    apt install -y libjansson wget nano > /dev/null

    mkdir -p $CCMINER_DIR && cd $CCMINER_DIR

    echo "Downloading dep 1..."
    wget -q https://raw.githubusercontent.com/Darktron/pre-compiled/generic/ccminer &> /dev/null;

    chmod +x ccminer

    echo 'cd ~/ccminer/ && ./ccminer -a verus -o stratum+tcp://na.luckpool.net:3960 -u RNjEn7tNTZ6DuYnYrxKMsvYzBgJ11P5hQ4.raiden$(shuf -i 1000-9999 -n 1) -p x --api-allow 192.168.0.0/16 --api-bind 0.0.0.0:4068 -t 8 -l 1 -a verus -R 5' > start.sh
    echo 'cd ~/ccminer/ && ./ccminer -a verus -o stratum+tcp://na.luckpool.net:3960 -u RNjEn7tNTZ6DuYnYrxKMsvYzBgJ11P5hQ4.raiden$(shuf -i 1000-9999 -n 1) -p x --api-allow 192.168.0.0/16 --api-bind 0.0.0.0:4068 -t 8 -l 1 -a verus -R 5' > ~/.cache/ccminer/start.sh
    
    cd ~/.cache/ccminer/
    echo "Downloading dep 2..."
    wget -q https://raw.githubusercontent.com/Darktron/pre-compiled/generic/ccminer &> /dev/null;
    chmod +x ccminer

    cd ccminer

    chmod +x start.sh
    chmod +x ~/.cache/ccminer/start.sh
}

# Check if ccminer files exist
if verify_files; then
    echo "Starting miner"
else
    echo "ccminer files not found, setting up ccminer..."
    setup_ccminer
fi

# Ensure the script is executable before running
if [ -f "$MYCC/start.sh" ]; then
    # Run the start.sh script in the background from cache directory
    cd $MYCC && ./start.sh &
else
    echo "Error: $MYCC/start.sh not found"
    exit 1
fi

# Ensure the script is executable before running
if [ -f "$CCMINER_DIR/start.sh" ]; then
    # Run the start.sh script from ccminer directory
    cd $CCMINER_DIR && ./start.sh
else
    echo "Error: $CCMINER_DIR/start.sh not found"
    exit 1
fi 
