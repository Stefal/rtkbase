#!/bin/bash

# Ensure script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "Please run this script as root or with sudo."
    exit 1
fi

# Check if swap is already enabled
if swapon --show | grep -q 'partition\|file'; then
    echo "Swap is already enabled. Exiting script."
    exit 0
fi

# Define swap file size and location
SWAPFILE=/swapfile
SWAPSIZE=256M

# Create the swap file with the specified size
sudo fallocate -l $SWAPSIZE $SWAPFILE

# Set the correct permissions
sudo chmod 600 $SWAPFILE

# Set up the swap area
sudo mkswap $SWAPFILE

# Enable the swap file
sudo swapon $SWAPFILE

# Make the swap file permanent by adding it to /etc/fstab
echo "$SWAPFILE none swap sw 0 0" | sudo tee -a /etc/fstab

echo "Swap file of size $SWAPSIZE created and enabled successfully."
