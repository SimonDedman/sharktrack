#!/bin/bash
# ==========================================
# SharkTrack Launcher for macOS
# Double-click this file to start SharkTrack
# ==========================================

# Change to the script's directory
cd "$(dirname "$0")"

echo ""
echo "=========================================="
echo "    SharkTrack - Marine Video Analysis"
echo "=========================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found!"
    echo ""
    echo "Please install Python 3:"
    echo "  Option 1: Install from https://www.python.org/downloads/"
    echo "  Option 2: Use Homebrew: brew install python3"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[OK] Python found: $(python3 --version)"

# Check for GPU support (MPS on Mac)
echo ""
echo "Checking GPU availability..."
python3 -c "
import torch
print('[OK] PyTorch version:', torch.__version__)
if torch.backends.mps.is_available():
    print('[OK] Apple Silicon GPU (MPS) available')
elif torch.cuda.is_available():
    print('[OK] CUDA GPU available:', torch.cuda.get_device_name(0))
else:
    print('[INFO] No GPU detected - using CPU (slower but works)')
" 2>/dev/null || echo "[INFO] PyTorch not yet installed - will be installed shortly"

# Create virtual environment if it doesn't exist
if [ ! -d "sharktrack-env" ]; then
    echo ""
    echo "Creating virtual environment (first-time setup)..."
    python3 -m venv sharktrack-env
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "[OK] Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source sharktrack-env/bin/activate

# Install/update dependencies
echo ""
echo "Checking dependencies (this may take a few minutes on first run)..."
pip install -q -r requirements.txt

# Install Flask if needed
pip show flask > /dev/null 2>&1 || pip install -q flask

# Create required directories
mkdir -p models templates static

# Check if config exists
if [ ! -f "sharktrack_config.json" ]; then
    echo ""
    echo "[INFO] Creating default configuration file..."
    python3 utils/config_loader.py --create
fi

echo ""
echo "=========================================="
echo "Starting SharkTrack Web Interface..."
echo "=========================================="
echo ""
echo "Your browser will open automatically."
echo "If not, navigate to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the web GUI
python3 start_sharktrack.py

# Keep terminal open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] SharkTrack failed to start"
    read -p "Press Enter to exit..."
fi
