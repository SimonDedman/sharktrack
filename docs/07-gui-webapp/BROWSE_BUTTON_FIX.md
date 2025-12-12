# Browse Button Troubleshooting

## Issue: Browse buttons do nothing in Firefox

### Root Cause
The browse buttons rely on the Flask web server being running. If the server isn't started, the JavaScript fetch() calls will fail silently.

### How to Test

#### 1. Check if Flask Server is Running

```bash
cd /home/simon/Installers/sharktrack-1.5

# Start the server
./launch_gui.sh

# OR manually:
source sharktrack-env/bin/activate
python3 web_gui.py
```

You should see:
```
============================================================
🦈 SharkTrack Web GUI
============================================================

Starting web server...
Open your browser to: http://localhost:5000

Press Ctrl+C to stop
============================================================
 * Serving Flask app 'web_gui'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

#### 2. Test the File Browser API Directly

With the server running, open a new terminal:

```bash
# Test the browse API endpoint
curl http://localhost:5000/api/files/browse?path=/home

# Should return JSON like:
# {"current_path":"/home","items":[...]}
```

If this works, the API is fine. If not, the server isn't running or crashed.

#### 3. Check Firefox Console for Errors

With server running and GUI open in Firefox:

1. Press `F12` to open Developer Tools
2. Click "Console" tab
3. Click a "Browse" button
4. Look for red error messages

**Common errors**:

##### Error: "Failed to fetch"
```
TypeError: NetworkError when attempting to fetch resource.
```
**Cause**: Server not running
**Fix**: Start `./launch_gui.sh` in terminal

##### Error: "openFileBrowser is not defined"
```
ReferenceError: openFileBrowser is not defined
```
**Cause**: JavaScript didn't load properly
**Fix**: Hard refresh Firefox (Ctrl+Shift+R)

##### Error: "CORS policy"
```
Access to fetch at 'http://localhost:5000/api/files/browse' from origin 'file://...' has been blocked by CORS policy
```
**Cause**: Opened HTML file directly instead of through Flask server
**Fix**: Must access via http://localhost:5000, not file://

#### 4. Verify JavaScript is Working

In Firefox console (F12), type:
```javascript
openFileBrowser('input_path', 'directory')
```

If nothing happens → JavaScript function exists but server isn't responding
If error → JavaScript not loaded

### Most Likely Cause

**You opened the HTML file directly** (file:///home/simon/.../index.html) instead of through the Flask server (http://localhost:5000).

The browse buttons REQUIRE the Flask server to be running because they fetch directory listings from the server.

### Correct Usage Workflow

```
Step 1: Start Flask server
  ./launch_gui.sh
  (Leaves terminal running with server)

Step 2: Browser opens automatically to http://localhost:5000
  (If not, manually go to http://localhost:5000)

Step 3: Click Browse buttons
  (Should now work because server is responding)
```

### Quick Test

```bash
# Terminal 1: Start server
cd /home/simon/Installers/sharktrack-1.5
./launch_gui.sh

# Terminal 2: Test API (while server running in Terminal 1)
curl http://localhost:5000/api/files/browse?path=/home

# Expected output:
{"current_path":"/home","items":[{"name":"simon","path":"/home/simon","type":"directory"},...]}
```

If curl works but Firefox buttons don't:
1. Check Firefox console for JavaScript errors
2. Try Chrome/Chromium to rule out browser-specific issue
3. Hard refresh Firefox (Ctrl+Shift+R)

### Fallback: Manual Path Entry

If browse buttons still don't work, you can:
1. Type paths directly in the text fields
2. Use tab completion in terminal to get correct paths
3. Copy-paste from file manager

Example paths:
```
Input: /media/simon/Extreme SSD/BRUV_Summer_2022_46_62
Output: /tmp/sharktrack_output
Species Classifier: models/my_classifier
```

### Alternative: Fix by Adding Error Messages

I can update the JavaScript to show clearer error messages when fetch() fails. Would you like me to do that?

The updated code would show alerts like:
- "Server not responding. Is web_gui.py running?"
- "Failed to load directory. Check server console for errors."
- "Permission denied accessing /path/to/directory"
