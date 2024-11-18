#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install the bot
echo "Installing bot..."
python3 setup.py develop

# Create systemd service
echo "Creating systemd service..."
python3 - <<EOF
from setup import create_systemd_service
create_systemd_service()
EOF

# Set correct permissions
echo "Setting permissions..."
chmod +x main.py

# Reload systemd
systemctl daemon-reload

echo -e "\nInstallation complete!"
echo "To start the bot, run:"
echo "sudo systemctl enable ollama-bot"
echo "sudo systemctl start ollama-bot"
echo -e "\nTo check status:"
echo "sudo systemctl status ollama-bot"