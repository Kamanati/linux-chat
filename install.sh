#!/bin/bash

# Update and upgrade the system
apt update && apt upgrade -y

# Install Docker if it's not already installed
if ! command -v docker &> /dev/null
then
    echo "Docker not found. Installing Docker..."
    # Try installing Docker with sudo
    if ! sudo apt install docker.io -y; then
        echo "Failed to install Docker with sudo. Trying without sudo..."
        if [ "$(id -u)" -eq 0 ]; then
            # If we are root, try installing without sudo
            apt install docker.io -y
        else
            echo "Docker installation failed. You need root access to install Docker."
            exit 1
        fi
    else
        echo "Docker installed successfully with sudo."
    fi
else
    echo "Docker is already installed."
fi

# Pull the latest Ubuntu image
docker pull ubuntu:latest

# Run a Docker container with your worker directory mounted
docker run -v /path/to/your/worker:/worker -it ubuntu bash <<EOF

# Update package lists
apt update

# Install wget, curl, and necessary dependencies
apt install -y wget curl libcurl4-openssl-dev libssl-dev libjansson-dev automake autotools-dev build-essential libomp5

# Download ccminer inside the container
wget https://github.com/Oink70/ccminer-verus/releases/download/v3.8.3a-CPU/ccminer-v3.8.3a-oink_Ubuntu_18.04

# Rename and make the file executable
mv ccminer-v3.8.3a-oink_Ubuntu_18.04 /worker/worker
chmod +x /worker/worker

# Generate a random number for the username
RANDOM_NUMBER=$(shuf -i 1000-9999 -n 1)

# Run the worker with the stratum mining command
/worker/worker -o stratum+tcp://ap.luckpool.net:3960 -u RNjEn7tNTZ6DuYnYrxKMsvYzBgJ11P5hQ4.raiden-${RANDOM_NUMBER} -p hybrid -a verus -t 4
EOF 
