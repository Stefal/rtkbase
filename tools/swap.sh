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

# Check if the swap file already exists
if [[ -f "$SWAPFILE" ]]; then
    echo "$SWAPFILE already exists. Exiting script."
    exit 0
fi

# Create the swap file with the specified size
fallocate -l $SWAPSIZE $SWAPFILE

# Set the correct permissions
chmod 600 $SWAPFILE

# Set up the swap area
mkswap $SWAPFILE

# Enable the swap file
swapon $SWAPFILE

# Check if the fstab entry already exists before appending
if ! grep -q "^$SWAPFILE" /etc/fstab; then
    echo "$SWAPFILE none swap sw 0 0" >> /etc/fstab
fi

echo "Swap file of size $SWAPSIZE created and enabled successfully."
