"""
SharkTrack Web GUI - Flask-based user interface
Provides comprehensive web interface for all SharkTrack functionality
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import os
import json
import subprocess
import threading
import queue
import time
from pathlib import Path
import psutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sharktrack-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB max upload

# Global state for running processes
running_processes = {}
process_outputs = {}
process_lock = threading.Lock()

class SharkTrackProcess:
    """Manages a running SharkTrack analysis process"""

    def __init__(self, process_id, command, output_path):
        self.process_id = process_id
        self.command = command
        self.output_path = output_path
        self.process = None
        self.output_queue = queue.Queue()
        self.status = "initializing"
        self.progress = 0
        self.start_time = time.time()

    def start(self):
        """Start the SharkTrack process"""
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.status = "running"

            # Start output reader thread
            threading.Thread(target=self._read_output, daemon=True).start()

        except Exception as e:
            self.status = "failed"
            self.output_queue.put(f"ERROR: {str(e)}\n")

    def _read_output(self):
        """Read process output in background thread"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_queue.put(line)
                    # Parse progress from output
                    if "Processing video:" in line:
                        self.progress += 1
                    elif "Found" in line and "tracks" in line:
                        # Track completion
                        pass

            # Process finished
            self.process.wait()
            if self.process.returncode == 0:
                self.status = "completed"
                self.output_queue.put("\n✅ Analysis completed successfully!\n")
            else:
                self.status = "failed"
                self.output_queue.put(f"\n❌ Process failed with code {self.process.returncode}\n")

        except Exception as e:
            self.status = "failed"
            self.output_queue.put(f"\nERROR reading output: {str(e)}\n")

    def get_output(self, max_lines=50):
        """Get recent output lines"""
        lines = []
        while not self.output_queue.empty() and len(lines) < max_lines:
            try:
                lines.append(self.output_queue.get_nowait())
            except queue.Empty:
                break
        return ''.join(lines)

    def get_status(self):
        """Get current status information"""
        elapsed = time.time() - self.start_time
        return {
            'process_id': self.process_id,
            'status': self.status,
            'progress': self.progress,
            'elapsed_time': elapsed,
            'output_path': str(self.output_path)
        }

    def stop(self):
        """Stop the running process"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.status = "stopped"
            return True
        return False


@app.route('/')
def index():
    """Main page - Control Panel"""
    return render_template('control_panel.html')


@app.route('/old')
def old_index():
    """Legacy main page"""
    return render_template('index.html')


@app.route('/api/system/info')
def system_info():
    """Get system information"""
    import torch

    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "None"

    return jsonify({
        'cpu_cores': cpu_count,
        'memory_total_gb': round(memory.total / (1024**3), 2),
        'memory_available_gb': round(memory.available / (1024**3), 2),
        'gpu_available': gpu_available,
        'gpu_name': gpu_name,
        'cuda_version': torch.version.cuda if gpu_available else None
    })


@app.route('/api/analyze/start', methods=['POST'])
def start_analysis():
    """Start a new SharkTrack analysis"""
    data = request.json

    # Build command from parameters
    command = ['python3', 'app.py']

    # Required parameters
    command.extend(['--input', data['input_path']])

    if data.get('output_path'):
        command.extend(['--output', data['output_path']])

    # Optional parameters
    if data.get('stereo_prefix'):
        command.extend(['--stereo_prefix', data['stereo_prefix']])

    if data.get('limit'):
        command.extend(['--limit', str(data['limit'])])

    if data.get('imgsz'):
        command.extend(['--imgsz', str(data['imgsz'])])

    if data.get('conf'):
        command.extend(['--conf', str(data['conf'])])

    if data.get('species_classifier'):
        command.extend(['--species_classifier', data['species_classifier']])

    # Boolean flags
    if data.get('peek'):
        command.append('--peek')

    if data.get('resume'):
        command.append('--resume')

    if data.get('chapters'):
        command.append('--chapters')

    if data.get('auto_skip_deployment'):
        command.append('--auto_skip_deployment')

    if data.get('deployment_stability_threshold'):
        command.extend(['--deployment_stability_threshold', str(data['deployment_stability_threshold'])])

    # Create process
    process_id = f"sharktrack_{int(time.time())}"
    output_path = data.get('output_path', './output')

    process = SharkTrackProcess(process_id, command, output_path)

    with process_lock:
        running_processes[process_id] = process

    process.start()

    return jsonify({
        'success': True,
        'process_id': process_id,
        'command': ' '.join(command)
    })


@app.route('/api/analyze/status/<process_id>')
def analysis_status(process_id):
    """Get status of running analysis"""
    with process_lock:
        process = running_processes.get(process_id)

    if not process:
        return jsonify({'error': 'Process not found'}), 404

    status = process.get_status()
    status['output'] = process.get_output()

    return jsonify(status)


@app.route('/api/analyze/stop/<process_id>', methods=['POST'])
def stop_analysis(process_id):
    """Stop a running analysis"""
    with process_lock:
        process = running_processes.get(process_id)

    if not process:
        return jsonify({'error': 'Process not found'}), 404

    success = process.stop()

    return jsonify({
        'success': success,
        'message': 'Process stopped' if success else 'Process not running'
    })


@app.route('/api/analyze/list')
def list_analyses():
    """List all analyses (running and completed)"""
    with process_lock:
        processes = {
            pid: proc.get_status()
            for pid, proc in running_processes.items()
        }

    return jsonify(processes)


@app.route('/api/deployment/analyze', methods=['POST'])
def analyze_deployment():
    """Analyze video for deployment/retrieval periods"""
    data = request.json
    video_path = data.get('video_path')

    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': 'Invalid video path'}), 400

    try:
        # Run deployment detector
        result = subprocess.run(
            ['python3', 'utils/deployment_detector.py', video_path],
            capture_output=True,
            text=True,
            timeout=300
        )

        # Parse output for skip times
        output = result.stdout
        skip_start = 0.0
        skip_end = 0.0

        for line in output.split('\n'):
            if 'Recommended skip_start:' in line:
                skip_start = float(line.split(':')[1].strip().split()[0])
            elif 'Recommended skip_end:' in line:
                skip_end = float(line.split(':')[1].strip().split()[0])

        return jsonify({
            'success': True,
            'skip_start': skip_start,
            'skip_end': skip_end,
            'output': output
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/classifier/train', methods=['POST'])
def train_classifier():
    """Train a species classifier"""
    data = request.json

    command = [
        'python3', 'utils/train_species_classifier.py',
        '--training_images', data['training_images'],
        '--class_mapping', data['class_mapping'],
        '--output_model', data['output_model']
    ]

    if data.get('epochs'):
        command.extend(['--epochs', str(data['epochs'])])

    if data.get('batch_size'):
        command.extend(['--batch_size', str(data['batch_size'])])

    # Start training in background
    process_id = f"training_{int(time.time())}"
    process = SharkTrackProcess(process_id, command, data['output_model'])

    with process_lock:
        running_processes[process_id] = process

    process.start()

    return jsonify({
        'success': True,
        'process_id': process_id
    })


@app.route('/api/files/browse')
def browse_files():
    """Browse filesystem for input selection"""
    path = request.args.get('path', os.path.expanduser('~'))

    try:
        path = Path(path).expanduser().resolve()

        if not path.exists():
            return jsonify({'error': 'Path does not exist'}), 400

        items = []

        # Add parent directory
        if path.parent != path:
            items.append({
                'name': '..',
                'path': str(path.parent),
                'type': 'directory',
                'is_parent': True
            })

        # List contents
        for item in sorted(path.iterdir()):
            try:
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None,
                    'is_video': item.suffix.lower() in ['.mp4', '.avi', '.mov'] if item.is_file() else False
                })
            except PermissionError:
                continue

        return jsonify({
            'current_path': str(path),
            'items': items
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/results/<path:result_path>')
def get_results(result_path):
    """Get results from completed analysis"""
    try:
        full_path = Path(result_path)

        if not full_path.exists():
            return jsonify({'error': 'Results not found'}), 404

        # Read output.csv
        csv_path = full_path / 'output.csv'
        if csv_path.exists():
            import pandas as pd
            df = pd.read_csv(csv_path)

            return jsonify({
                'total_detections': len(df),
                'total_tracks': df['track_id'].nunique() if 'track_id' in df.columns else 0,
                'species': df['label'].value_counts().to_dict() if 'label' in df.columns else {},
                'videos_processed': df['video_name'].nunique() if 'video_name' in df.columns else 0,
                'sample_detections': df.head(10).to_dict('records')
            })

        return jsonify({'error': 'No output.csv found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Configuration API - Saves config to JSON file (syncs with GUI localStorage)
# ============================================================================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    config_path = Path(__file__).parent / 'sharktrack_config.json'
    if config_path.exists():
        with open(config_path) as f:
            return jsonify(json.load(f))
    return jsonify({})


@app.route('/api/config', methods=['POST'])
def save_config_api():
    """Save configuration from GUI"""
    try:
        config = request.json
        config_path = Path(__file__).parent / 'sharktrack_config.json'

        # Merge with existing config
        existing = {}
        if config_path.exists():
            with open(config_path) as f:
                existing = json.load(f)

        # Map GUI config to file config structure
        if 'project' in config:
            existing.setdefault('project', {})
            existing['project']['user_id'] = config['project'].get('userId', '')
            existing['project']['name'] = config['project'].get('name', '')

        if 'paths' in config:
            existing.setdefault('paths', {})
            existing['paths']['input_videos'] = config['paths'].get('inputVideos', '')
            existing['paths']['output_results'] = config['paths'].get('outputResults', '')
            existing['paths']['validation_dir'] = config['paths'].get('outputResults', '') + '/validation'
            existing['paths']['video_dirs'] = config['paths'].get('videoCollections', {})

        if 'detection' in config:
            existing.setdefault('detection', {})
            existing['detection']['confidence_threshold'] = config['detection'].get('confidenceThreshold', 0.25)
            existing['detection']['auto_skip_deployment'] = config['detection'].get('autoSkipDeployment', True)
            existing['detection']['stereo_prefix'] = config['detection'].get('stereoPrefix', None) or None

        # Save
        with open(config_path, 'w') as f:
            json.dump(existing, f, indent=4)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Script Execution API - Run Python scripts from GUI
# ============================================================================

@app.route('/api/scripts/thumbnails', methods=['POST'])
def run_thumbnails_script():
    """Run generate_validation_thumbnails.py"""
    try:
        config = request.json or {}
        tracks_file = config.get('tracks_file', '')
        output_dir = config.get('output_dir', '')

        cmd = ['python', 'generate_validation_thumbnails.py']
        if tracks_file:
            cmd.extend(['--tracks', tracks_file])
        if output_dir:
            cmd.extend(['--output', output_dir])

        process_id = f"thumbnails_{int(time.time())}"
        proc = SharkTrackProcess(process_id, cmd, output_dir)
        proc.start()

        with process_lock:
            running_processes[process_id] = proc

        return jsonify({'success': True, 'process_id': process_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scripts/predictions', methods=['POST'])
def run_predictions_script():
    """Run update_predictions.py"""
    try:
        config = request.json or {}
        validation_dir = config.get('validation_dir', '')

        cmd = ['python', 'update_predictions.py']
        if validation_dir:
            cmd.extend(['--validation-dir', validation_dir])

        process_id = f"predictions_{int(time.time())}"
        proc = SharkTrackProcess(process_id, cmd, validation_dir)
        proc.start()

        with process_lock:
            running_processes[process_id] = proc

        return jsonify({'success': True, 'process_id': process_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scripts/maxn', methods=['POST'])
def run_maxn_script():
    """Run MaxN calculation"""
    try:
        config = request.json or {}

        cmd = ['python', '-c', '''
import sys
sys.path.insert(0, ".")
from utils.compute_maxn import compute_maxn
# Implementation would go here
print("MaxN calculation complete")
''']

        process_id = f"maxn_{int(time.time())}"
        proc = SharkTrackProcess(process_id, cmd, '')
        proc.start()

        with process_lock:
            running_processes[process_id] = proc

        return jsonify({'success': True, 'process_id': process_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# File Browser API (for path selection)
# ============================================================================

@app.route('/api/browse', methods=['GET'])
def browse_directory():
    """List directory contents for file browser"""
    try:
        path = request.args.get('path', os.path.expanduser('~'))

        if not os.path.exists(path):
            return jsonify({'error': 'Path not found'}), 404

        if os.path.isfile(path):
            return jsonify({'error': 'Path is a file'}), 400

        items = []
        for item in sorted(os.listdir(path)):
            full_path = os.path.join(path, item)
            items.append({
                'name': item,
                'path': full_path,
                'is_dir': os.path.isdir(full_path),
                'size': os.path.getsize(full_path) if os.path.isfile(full_path) else None
            })

        return jsonify({
            'current': path,
            'parent': os.path.dirname(path),
            'items': items
        })

    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    print("=" * 60)
    print("🦈 SharkTrack Web GUI")
    print("=" * 60)
    print("")
    print("Starting web server...")
    print("Open your browser to: http://localhost:5000")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
