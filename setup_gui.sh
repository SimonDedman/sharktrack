#!/bin/bash
#
# SharkTrack Web GUI Setup Script
# Installs dependencies and launches the web interface
#

echo "=========================================="
echo "SharkTrack Web GUI Setup"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "sharktrack-env" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create it first:"
    echo "  python3 -m venv sharktrack-env"
    echo "  source sharktrack-env/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source sharktrack-env/bin/activate

# Install Flask if not present
echo "📦 Checking Flask installation..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing Flask..."
    pip install flask
else
    echo "✅ Flask already installed"
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p templates
mkdir -p static
mkdir -p models

# Desktop launcher for this install location (git-ignored; template keeps no personal paths)
if [ -f SharkTrack.desktop.template ]; then
    sed "s#@INSTALL_DIR@#$(pwd)#g" SharkTrack.desktop.template > SharkTrack.desktop
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "=========================================="
echo "🚀 Starting SharkTrack Web GUI..."
echo "=========================================="
echo ""
echo "Open your browser to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Launch web GUI
python3 web_gui.py
