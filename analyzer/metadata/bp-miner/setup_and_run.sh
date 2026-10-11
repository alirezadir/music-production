#!/bin/bash
# Setup and run script for Beatport Label Miner

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "Beatport Label Miner - Setup & Run"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Install dependencies using uv if available, otherwise pip
if command -v uv &> /dev/null; then
    echo "Installing dependencies with uv..."
    uv pip install -r requirements.txt
else
    echo "Installing dependencies with pip..."
    pip3 install -r requirements.txt --user
fi

echo ""
echo "Dependencies installed!"
echo ""

# Check if config exists
if [ ! -f "config.json" ]; then
    echo "Error: config.json not found"
    exit 1
fi

echo "Configuration found:"
cat config.json | python3 -m json.tool
echo ""

# Run the pipeline
echo "=========================================="
echo "Starting pipeline..."
echo "=========================================="
echo ""

python3 run_full_pipeline.py

echo ""
echo "=========================================="
echo "Pipeline completed!"
echo "=========================================="

