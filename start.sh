#!/bin/bash

# Startup script for Fac Habitat Scraper
# Usage: ./start.sh

echo "Starting Fac Habitat scraper..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file missing. Copy .env.example to .env and configure it."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies if requirements.txt changed
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the scraper
echo "Running scraper..."
python main.py

echo "Scraping completed!"