#!/bin/bash
#
# SharkTrack Web GUI Launcher
# Opens browser automatically after starting server
#

cd "$(dirname "$0")"

echo "=========================================="
echo "🦈 SharkTrack Web GUI"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "sharktrack-env" ]; then
    echo "❌ Virtual environment not found!"
    echo ""
    echo "Setting up for first time..."
    python3 -m venv sharktrack-env
    source sharktrack-env/bin/activate
    pip install flask torch torchvision ultralytics opencv-python pandas tqdm click scikit-learn
else
    source sharktrack-env/bin/activate
fi

# Install Flask if needed
python3 -c "import flask" 2>/dev/null || pip install flask

# Create directories
mkdir -p templates static models

echo "✅ Starting server..."
echo ""

# Start server in background
python3 web_gui.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Open browser
echo "🌐 Opening browser..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:5000
elif command -v gnome-open > /dev/null; then
    gnome-open http://localhost:5000
else
    echo "Please open your browser to: http://localhost:5000"
fi

echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Wait for server process
wait $SERVER_PID
