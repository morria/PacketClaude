#!/bin/bash
# Run PacketClaude

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Check for config file
if [ ! -f "config/config.yaml" ]; then
    echo "Error: config/config.yaml not found"
    echo "Please copy config/config.yaml.example to config/config.yaml and configure it"
    exit 1
fi

# Check for .env file (supports regular files and named pipes from 1Password)
if [ ! -e ".env" ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and add your Anthropic API key"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run PacketClaude
python -m src.packetclaude.main "$@"
