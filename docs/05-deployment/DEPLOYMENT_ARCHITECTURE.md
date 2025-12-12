# SharkTrack Deployment Architecture

## Overview

Complete deployment architecture for transforming SharkTrack from a local video processing tool into a global marine research platform with web portals, mobile apps, blockchain infrastructure, and BitTorrent indexing services.

------------------------------------------------------------------------

## 🌐 Web Platform Architecture

### GitHub Repository Structure

```         
sharktrack-platform/
├── README.md                          # Main project overview
├── docs/                              # Documentation and vision
│   ├── PROJECT_VISION_INDEX.md        # Strategic overview
│   ├── INTERACTIVE_REVIEW_PLATFORM.md # User platform specs
│   ├── DISTRIBUTED_VIDEO_NETWORK.md   # P2P infrastructure
│   ├── COLLECTIVE_SPECIES_INTELLIGENCE.md # AI knowledge specs
│   └── api/                           # API documentation
├── core/                              # Core SharkTrack processing
│   ├── app.py                         # Main detection application
│   ├── utils/                         # Processing utilities
│   ├── models/                        # AI models
│   └── requirements.txt               # Dependencies
├── web-platform/                      # Web application
│   ├── frontend/                      # React/Vue.js frontend
│   ├── backend/                       # Django/FastAPI backend
│   ├── database/                      # Schema and migrations
│   └── docker/                        # Containerization
├── mobile-apps/                       # Mobile applications
│   ├── android/                       # Android (Kotlin/Java)
│   ├── ios/                          # iOS (Swift)
│   └── shared/                       # Shared components
├── infrastructure/                    # Deployment infrastructure
│   ├── bittorrent-tracker/           # BitTorrent indexing
│   ├── blockchain-node/              # Shark knowledge blockchain
│   ├── kubernetes/                   # K8s deployment configs
│   └── terraform/                    # Infrastructure as code
├── scripts/                          # Automation and utilities
│   ├── deployment/                   # Deployment automation
│   ├── data-migration/               # Data import/export
│   └── monitoring/                   # Health checks and metrics
└── tests/                            # Test suites
    ├── unit/                         # Unit tests
    ├── integration/                  # Integration tests
    └── e2e/                         # End-to-end tests
```

### GitHub Pages Website (sharktrack-platform.github.io)

``` html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SharkTrack Global Platform</title>
    <link rel="stylesheet" href="styles/main.css">
</head>
<body>
    <!-- Hero Section -->
    <section class="hero">
        <h1>SharkTrack Global Platform</h1>
        <p>Transforming marine research through AI, collaboration, and collective intelligence</p>
        <div class="cta-buttons">
            <a href="https://app.sharktrack.org" class="btn-primary">Launch Platform</a>
            <a href="https://docs.sharktrack.org" class="btn-secondary">Documentation</a>
        </div>
    </section>

    <!-- Live Statistics Dashboard -->
    <section class="stats-dashboard">
        <div class="stat-card">
            <h3>Videos Processed</h3>
            <span id="videos-processed" class="stat-number">Loading...</span>
        </div>
        <div class="stat-card">
            <h3>Species Detected</h3>
            <span id="species-detected" class="stat-number">Loading...</span>
        </div>
        <div class="stat-card">
            <h3>Active Researchers</h3>
            <span id="active-researchers" class="stat-number">Loading...</span>
        </div>
        <div class="stat-card">
            <h3>Global Institutions</h3>
            <span id="institutions" class="stat-number">Loading...</span>
        </div>
    </section>

    <!-- Platform Features -->
    <section class="features">
        <div class="feature-grid">
            <div class="feature-card">
                <h3>🎥 Video Processing</h3>
                <p>AI-powered shark detection and tracking in underwater videos</p>
                <a href="/upload">Upload Videos</a>
            </div>
            <div class="feature-card">
                <h3>🌐 Collaborative Review</h3>
                <p>Global researcher network for species validation</p>
                <a href="/review">Start Reviewing</a>
            </div>
            <div class="feature-card">
                <h3>📊 Live Analytics</h3>
                <p>Real-time ecosystem monitoring and species tracking</p>
                <a href="/analytics">View Dashboard</a>
            </div>
            <div class="feature-card">
                <h3>🧠 Species Intelligence</h3>
                <p>Collective AI models that grow with each contribution</p>
                <a href="/intelligence">Explore Models</a>
            </div>
        </div>
    </section>

    <!-- Quick Upload Portal -->
    <section class="quick-upload">
        <h2>Quick Data Upload</h2>
        <div class="upload-options">
            <div class="webcam-upload">
                <h3>📹 Webcam Capture</h3>
                <video id="webcam-preview" autoplay muted></video>
                <button id="start-recording">Start Recording</button>
                <button id="upload-clip">Upload Clip</button>
            </div>
            <div class="file-upload">
                <h3>📁 File Upload</h3>
                <div class="drop-zone" id="file-drop-zone">
                    <p>Drag & drop videos here or click to browse</p>
                    <input type="file" id="file-input" multiple accept="video/*">
                </div>
            </div>
        </div>
    </section>

    <script src="js/stats-updater.js"></script>
    <script src="js/webcam-handler.js"></script>
    <script src="js/file-upload.js"></script>
</body>
</html>
```

### Live Statistics API

``` javascript
// js/stats-updater.js
class LiveStatsUpdater {
    constructor() {
        this.apiBase = 'https://api.sharktrack.org';
        this.updateInterval = 30000; // 30 seconds
        this.startUpdating();
    }

    async updateStats() {
        try {
            const response = await fetch(`${this.apiBase}/stats/live`);
            const stats = await response.json();

            document.getElementById('videos-processed').textContent =
                this.formatNumber(stats.videos_processed);
            document.getElementById('species-detected').textContent =
                stats.unique_species;
            document.getElementById('active-researchers').textContent =
                stats.active_researchers_24h;
            document.getElementById('institutions').textContent =
                stats.participating_institutions;

        } catch (error) {
            console.error('Failed to update stats:', error);
        }
    }

    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    startUpdating() {
        this.updateStats(); // Initial load
        setInterval(() => this.updateStats(), this.updateInterval);
    }
}

new LiveStatsUpdater();
```

### Webcam Upload Handler

``` javascript
// js/webcam-handler.js
class WebcamUploader {
    constructor() {
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.stream = null;
        this.setupEventListeners();
    }

    async setupEventListeners() {
        const startBtn = document.getElementById('start-recording');
        const uploadBtn = document.getElementById('upload-clip');
        const video = document.getElementById('webcam-preview');

        startBtn.addEventListener('click', () => this.toggleRecording());
        uploadBtn.addEventListener('click', () => this.uploadRecording());

        // Initialize webcam
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 1920, height: 1080 },
                audio: true
            });
            video.srcObject = this.stream;
        } catch (error) {
            console.error('Webcam access failed:', error);
        }
    }

    toggleRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    startRecording() {
        this.recordedChunks = [];
        this.mediaRecorder = new MediaRecorder(this.stream);

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.recordedChunks.push(event.data);
            }
        };

        this.mediaRecorder.start();
        document.getElementById('start-recording').textContent = 'Stop Recording';
    }

    stopRecording() {
        this.mediaRecorder.stop();
        document.getElementById('start-recording').textContent = 'Start Recording';
    }

    async uploadRecording() {
        if (this.recordedChunks.length === 0) return;

        const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
        const formData = new FormData();
        formData.append('video', blob, 'webcam-recording.webm');
        formData.append('source', 'webcam');
        formData.append('timestamp', new Date().toISOString());

        // Get GPS location if available
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                formData.append('latitude', position.coords.latitude);
                formData.append('longitude', position.coords.longitude);
                this.performUpload(formData);
            });
        } else {
            this.performUpload(formData);
        }
    }

    async performUpload(formData) {
        try {
            const response = await fetch('https://api.sharktrack.org/upload/video', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                alert(`Upload successful! Processing ID: ${result.processing_id}`);
                this.recordedChunks = [];
            } else {
                alert('Upload failed. Please try again.');
            }
        } catch (error) {
            console.error('Upload error:', error);
            alert('Upload failed. Please check your connection.');
        }
    }
}

new WebcamUploader();
```

------------------------------------------------------------------------

## 🔗 BitTorrent Index Server

### Server Architecture

``` python
# infrastructure/bittorrent-tracker/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import bencodepy
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis

app = FastAPI(title="SharkTrack BitTorrent Index", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

Base = declarative_base()
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class MarineDatasetTorrent(Base):
    __tablename__ = "marine_torrents"

    info_hash = Column(String(40), primary_key=True)
    dataset_name = Column(String(255))
    institution = Column(String(255))
    magnet_link = Column(String(1000))
    total_size_gb = Column(Float)
    video_count = Column(Integer)
    species_list = Column(String(1000))  # JSON array of species
    geographic_region = Column(String(255))
    depth_range = Column(String(100))
    deployment_date = Column(DateTime)
    created_at = Column(DateTime)
    seeders = Column(Integer, default=0)
    leechers = Column(Integer, default=0)

@app.post("/register-torrent")
async def register_torrent(torrent_data: dict):
    """
    Register new marine research dataset torrent
    """
    # Validate torrent file
    torrent_bytes = bytes.fromhex(torrent_data['torrent_hex'])
    torrent_dict = bencodepy.decode(torrent_bytes)

    # Calculate info hash
    info_bytes = bencodepy.encode(torrent_dict[b'info'])
    info_hash = hashlib.sha1(info_bytes).hexdigest()

    # Extract metadata
    dataset_metadata = torrent_dict.get(b'research_metadata', {})

    # Store in database
    torrent_record = MarineDatasetTorrent(
        info_hash=info_hash,
        dataset_name=dataset_metadata.get(b'dataset_name', b'').decode(),
        institution=dataset_metadata.get(b'institution', b'').decode(),
        magnet_link=generate_magnet_link(info_hash, torrent_dict),
        total_size_gb=calculate_total_size(torrent_dict) / (1024**3),
        video_count=count_video_files(torrent_dict),
        species_list=dataset_metadata.get(b'species_list', b'').decode(),
        geographic_region=dataset_metadata.get(b'region', b'').decode(),
        depth_range=dataset_metadata.get(b'depth_range', b'').decode()
    )

    # Cache for fast lookups
    redis_client.hset(f"torrent:{info_hash}", mapping=torrent_record.__dict__)

    return {"status": "registered", "info_hash": info_hash}

@app.get("/search-datasets")
async def search_datasets(species: str = None, region: str = None,
                         institution: str = None, min_size_gb: float = None):
    """
    Search marine research datasets
    """
    # Build search query
    query_filters = []
    if species:
        query_filters.append(f"species_list LIKE '%{species}%'")
    if region:
        query_filters.append(f"geographic_region LIKE '%{region}%'")
    if institution:
        query_filters.append(f"institution LIKE '%{institution}%'")
    if min_size_gb:
        query_filters.append(f"total_size_gb >= {min_size_gb}")

    # Execute search and return results
    # Implementation details...

@app.get("/torrent/{info_hash}/peers")
async def get_torrent_peers(info_hash: str):
    """
    BitTorrent tracker announce endpoint
    """
    # Standard BitTorrent tracker protocol
    # Return peer list for this torrent

@app.post("/announce")
async def announce(request: dict):
    """
    BitTorrent announce endpoint for peer discovery
    """
    # Handle standard BitTorrent announce protocol
    # Update seeder/leecher counts
    # Return peer list

def generate_magnet_link(info_hash: str, torrent_dict: dict) -> str:
    """Generate magnet link for torrent"""
    announce_urls = torrent_dict.get(b'announce-list', [[torrent_dict.get(b'announce')]])
    trackers = '&'.join([f"tr={url[0].decode()}" for url in announce_urls if url])
    return f"magnet:?xt=urn:btih:{info_hash}&{trackers}"
```

### Marine Dataset Discovery API

``` python
# infrastructure/bittorrent-tracker/discovery.py
@app.get("/discover/similar-environments")
async def discover_similar_environments(depth: float, temperature: float,
                                      location: tuple, radius_km: float = 50):
    """
    Find datasets from similar environmental conditions
    """
    similar_datasets = []

    # Search for datasets within geographic radius
    for torrent in get_nearby_torrents(location, radius_km):
        env_similarity = calculate_environmental_similarity(
            target_depth=depth,
            target_temp=temperature,
            dataset_conditions=torrent.environmental_metadata
        )

        if env_similarity > 0.7:  # 70% similarity threshold
            similar_datasets.append({
                'torrent': torrent,
                'similarity_score': env_similarity,
                'magnet_link': torrent.magnet_link
            })

    return sorted(similar_datasets, key=lambda x: x['similarity_score'], reverse=True)

@app.get("/discover/species-hotspots")
async def discover_species_hotspots(species: str):
    """
    Find geographic hotspots for specific species
    """
    species_observations = get_species_observations(species)

    # Cluster observations geographically
    hotspots = geographic_clustering(species_observations)

    # Find available datasets for each hotspot
    hotspot_datasets = []
    for hotspot in hotspots:
        datasets = get_datasets_in_region(hotspot.center, hotspot.radius)
        hotspot_datasets.append({
            'location': hotspot.center,
            'observation_density': hotspot.density,
            'available_datasets': len(datasets),
            'total_data_gb': sum(d.total_size_gb for d in datasets),
            'magnet_links': [d.magnet_link for d in datasets]
        })

    return hotspot_datasets
```

------------------------------------------------------------------------

## ⛓️ Blockchain Infrastructure

### Shark Knowledge Blockchain Node

``` python
# infrastructure/blockchain-node/shark_chain.py
from blockchain import Blockchain, Block
from flask import Flask, request, jsonify
import hashlib
import json
from datetime import datetime

app = Flask(__name__)
shark_knowledge_chain = Blockchain()

class KnowledgeContribution:
    def __init__(self, contributor_id: str, species_id: str,
                 knowledge_type: str, data_hash: str, metadata: dict):
        self.contributor_id = contributor_id
        self.species_id = species_id
        self.knowledge_type = knowledge_type  # 'morphological', 'behavioral', 'environmental'
        self.data_hash = data_hash
        self.metadata = metadata
        self.timestamp = datetime.now().isoformat()
        self.validation_signatures = []

    def to_dict(self):
        return self.__dict__

class SharkKnowledgeBlock(Block):
    def __init__(self, contributions: list, previous_hash: str):
        self.contributions = contributions
        self.scientific_proof = self.generate_scientific_proof()
        super().__init__(json.dumps([c.to_dict() for c in contributions]), previous_hash)

    def generate_scientific_proof(self):
        """
        Generate proof-of-science for contributions
        Validates scientific methodology and peer review
        """
        proof_score = 0
        for contribution in self.contributions:
            # Check peer validation signatures
            peer_score = len(contribution.validation_signatures) * 10

            # Check data quality metrics
            quality_score = contribution.metadata.get('confidence_score', 0) * 50

            # Check institutional credibility
            institution_score = get_institution_credibility(
                contribution.metadata.get('institution', '')
            ) * 20

            proof_score += peer_score + quality_score + institution_score

        return proof_score

@app.route('/contribute', methods=['POST'])
def submit_contribution():
    """
    Submit new knowledge contribution to blockchain
    """
    data = request.json

    contribution = KnowledgeContribution(
        contributor_id=data['contributor_id'],
        species_id=data['species_id'],
        knowledge_type=data['knowledge_type'],
        data_hash=data['data_hash'],
        metadata=data['metadata']
    )

    # Add to pending contributions pool
    pending_contributions.append(contribution)

    return jsonify({
        'status': 'pending_validation',
        'contribution_id': contribution.data_hash,
        'next_block_in': estimate_next_block_time()
    })

@app.route('/validate', methods=['POST'])
def validate_contribution():
    """
    Peer validation of contributions
    """
    data = request.json
    contribution_id = data['contribution_id']
    validator_signature = data['validator_signature']
    validation_score = data['validation_score']  # 1-5 scale

    # Find contribution in pending pool
    contribution = find_contribution(contribution_id)
    if contribution:
        contribution.validation_signatures.append({
            'validator': validator_signature,
            'score': validation_score,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({'status': 'validation_recorded'})

    return jsonify({'error': 'contribution_not_found'}), 404

@app.route('/mine', methods=['POST'])
def mine_knowledge_block():
    """
    Mine new block with validated contributions
    """
    # Select contributions with sufficient validation
    validated_contributions = [
        c for c in pending_contributions
        if len(c.validation_signatures) >= 3  # Minimum 3 peer validations
        and average_validation_score(c) >= 3.5  # Minimum 3.5/5 score
    ]

    if validated_contributions:
        # Create new block
        new_block = SharkKnowledgeBlock(
            contributions=validated_contributions,
            previous_hash=shark_knowledge_chain.get_latest_block().hash
        )

        # Add to chain
        shark_knowledge_chain.add_block(new_block)

        # Remove from pending
        for contribution in validated_contributions:
            pending_contributions.remove(contribution)

        # Distribute rewards to contributors and validators
        distribute_knowledge_tokens(validated_contributions)

        return jsonify({
            'status': 'block_mined',
            'block_hash': new_block.hash,
            'contributions_count': len(validated_contributions)
        })

    return jsonify({'error': 'insufficient_validated_contributions'}), 400

@app.route('/species/{species_id}/knowledge', methods=['GET'])
def get_species_knowledge(species_id):
    """
    Retrieve all knowledge contributions for a species
    """
    species_knowledge = []

    for block in shark_knowledge_chain.chain:
        if hasattr(block, 'contributions'):
            for contribution in block.contributions:
                if contribution.species_id == species_id:
                    species_knowledge.append({
                        'contribution': contribution.to_dict(),
                        'block_hash': block.hash,
                        'block_timestamp': block.timestamp,
                        'validation_count': len(contribution.validation_signatures)
                    })

    return jsonify({
        'species_id': species_id,
        'total_contributions': len(species_knowledge),
        'knowledge_history': species_knowledge
    })
```

### Knowledge Token Economics

``` python
# infrastructure/blockchain-node/token_economics.py
class KnowledgeTokenSystem:
    def __init__(self):
        self.token_balances = {}  # contributor_id -> token_balance
        self.contribution_rewards = {
            'novel_species': 1000,
            'rare_behavior': 500,
            'morphological_data': 100,
            'environmental_data': 50,
            'validation': 25
        }

    def calculate_contribution_reward(self, contribution: KnowledgeContribution) -> int:
        """
        Calculate token reward for knowledge contribution
        """
        base_reward = self.contribution_rewards.get(
            contribution.knowledge_type, 50
        )

        # Novelty multiplier
        novelty_score = contribution.metadata.get('novelty_score', 1.0)

        # Quality multiplier
        quality_score = contribution.metadata.get('confidence_score', 0.5)

        # Scarcity multiplier (more reward for understudied species/regions)
        scarcity_score = calculate_data_scarcity(
            contribution.species_id,
            contribution.metadata.get('location')
        )

        total_reward = int(base_reward * novelty_score * quality_score * scarcity_score)
        return total_reward

    def distribute_rewards(self, contributions: list):
        """
        Distribute tokens to contributors and validators
        """
        for contribution in contributions:
            # Reward contributor
            contributor_reward = self.calculate_contribution_reward(contribution)
            self.add_tokens(contribution.contributor_id, contributor_reward)

            # Reward validators
            validator_reward = contributor_reward // 10  # 10% of contributor reward
            for validation in contribution.validation_signatures:
                self.add_tokens(validation['validator'], validator_reward)

    def add_tokens(self, user_id: str, amount: int):
        """Add tokens to user balance"""
        self.token_balances[user_id] = self.token_balances.get(user_id, 0) + amount
```

------------------------------------------------------------------------

## 📱 Mobile Applications

### Android App Architecture

``` kotlin
// mobile-apps/android/app/src/main/java/org/sharktrack/MainActivity.kt
package org.sharktrack

import android.Manifest
import android.content.pm.PackageManager
import android.location.Location
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : ComponentActivity() {
    private lateinit var cameraProvider: ProcessCameraProvider
    private var videoCapture: VideoCapture<Recorder>? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request permissions
        requestCameraPermissions()

        setContent {
            SharkTrackTheme {
                MainApp()
            }
        }
    }

    @Composable
    fun MainApp() {
        var selectedTab by remember { mutableStateOf(0) }

        Scaffold(
            bottomBar = {
                NavigationBar {
                    NavigationBarItem(
                        icon = { Icon(Icons.Default.Camera, contentDescription = "Record") },
                        label = { Text("Record") },
                        selected = selectedTab == 0,
                        onClick = { selectedTab = 0 }
                    )
                    NavigationBarItem(
                        icon = { Icon(Icons.Default.Upload, contentDescription = "Upload") },
                        label = { Text("Upload") },
                        selected = selectedTab == 1,
                        onClick = { selectedTab = 1 }
                    )
                    NavigationBarItem(
                        icon = { Icon(Icons.Default.Analytics, contentDescription = "Stats") },
                        label = { Text("My Stats") },
                        selected = selectedTab == 2,
                        onClick = { selectedTab = 2 }
                    )
                    NavigationBarItem(
                        icon = { Icon(Icons.Default.PlayCircle, contentDescription = "Watch") },
                        label = { Text("Watch") },
                        selected = selectedTab == 3,
                        onClick = { selectedTab = 3 }
                    )
                }
            }
        ) { paddingValues ->
            when (selectedTab) {
                0 -> RecordingScreen(paddingValues)
                1 -> UploadScreen(paddingValues)
                2 -> PersonalStatsScreen(paddingValues)
                3 -> VideoWatchScreen(paddingValues)
            }
        }
    }

    @Composable
    fun RecordingScreen(paddingValues: PaddingValues) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Camera preview
            AndroidView(
                factory = { context ->
                    PreviewView(context).apply {
                        setupCamera()
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            )

            // Recording controls
            Row(
                modifier = Modifier.padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Button(
                    onClick = { startRecording() },
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Start Recording")
                }

                Button(
                    onClick = { stopRecording() },
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Stop Recording")
                }
            }

            // GPS and metadata display
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Location: Loading GPS...")
                    Text("Depth: Enter manually")
                    Text("Water temp: Enter manually")
                }
            }
        }
    }

    @Composable
    fun PersonalStatsScreen(paddingValues: PaddingValues) {
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                StatsCard(
                    title = "Videos Uploaded",
                    value = "42",
                    subtitle = "This month: 7"
                )
            }

            item {
                StatsCard(
                    title = "Species Identified",
                    value = "15",
                    subtitle = "Most recent: Tiger Shark"
                )
            }

            item {
                StatsCard(
                    title = "Knowledge Points",
                    value = "2,847",
                    subtitle = "Rank: #23 globally"
                )
            }

            item {
                StatsCard(
                    title = "Validations Made",
                    value = "156",
                    subtitle = "Accuracy: 94.2%"
                )
            }
        }
    }

    @Composable
    fun StatsCard(title: String, value: String, subtitle: String) {
        Card(
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.headlineSmall
                )
                Text(
                    text = value,
                    style = MaterialTheme.typography.displayMedium,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }

    private fun setupCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            cameraProvider = cameraProviderFuture.get()
            bindCameraUseCases()
        }, ContextCompat.getMainExecutor(this))
    }

    private fun bindCameraUseCases() {
        val preview = Preview.Builder().build()
        val recorder = Recorder.Builder()
            .setQualitySelector(QualitySelector.from(Quality.HIGHEST))
            .build()
        videoCapture = VideoCapture.withOutput(recorder)

        val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

        try {
            cameraProvider.unbindAll()
            cameraProvider.bindToLifecycle(
                this, cameraSelector, preview, videoCapture
            )
        } catch (exc: Exception) {
            // Handle camera binding errors
        }
    }
}
```

### iOS App Architecture

``` swift
// mobile-apps/ios/SharkTrack/ContentView.swift
import SwiftUI
import AVFoundation
import CoreLocation

struct ContentView: View {
    @StateObject private var cameraManager = CameraManager()
    @StateObject private var locationManager = LocationManager()
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            RecordingView()
                .tabItem {
                    Image(systemName: "camera")
                    Text("Record")
                }
                .tag(0)

            UploadView()
                .tabItem {
                    Image(systemName: "icloud.and.arrow.up")
                    Text("Upload")
                }
                .tag(1)

            PersonalStatsView()
                .tabItem {
                    Image(systemName: "chart.bar")
                    Text("My Stats")
                }
                .tag(2)

            VideoWatchView()
                .tabItem {
                    Image(systemName: "play.circle")
                    Text("Watch")
                }
                .tag(3)
        }
        .environmentObject(cameraManager)
        .environmentObject(locationManager)
    }
}

struct RecordingView: View {
    @EnvironmentObject var cameraManager: CameraManager
    @EnvironmentObject var locationManager: LocationManager
    @State private var isRecording = false

    var body: some View {
        VStack {
            // Camera preview
            CameraPreview(cameraManager: cameraManager)
                .aspectRatio(16/9, contentMode: .fit)
                .cornerRadius(10)
                .padding()

            // Recording controls
            HStack(spacing: 20) {
                Button(action: {
                    if isRecording {
                        cameraManager.stopRecording()
                    } else {
                        cameraManager.startRecording()
                    }
                    isRecording.toggle()
                }) {
                    Text(isRecording ? "Stop Recording" : "Start Recording")
                        .foregroundColor(.white)
                        .padding()
                        .background(isRecording ? Color.red : Color.blue)
                        .cornerRadius(10)
                }
            }

            // Metadata display
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Location:")
                    Spacer()
                    Text(locationManager.locationString)
                        .foregroundColor(.secondary)
                }

                HStack {
                    Text("Depth (m):")
                    Spacer()
                    TextField("Enter depth", text: .constant(""))
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .frame(width: 100)
                }

                HStack {
                    Text("Water temp (°C):")
                    Spacer()
                    TextField("Enter temp", text: .constant(""))
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .frame(width: 100)
                }
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(10)
            .padding()

            Spacer()
        }
        .navigationTitle("Record Video")
    }
}

struct PersonalStatsView: View {
    @State private var stats = UserStats()

    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 16) {
                    StatsCard(
                        title: "Videos Uploaded",
                        value: "\(stats.videosUploaded)",
                        subtitle: "This month: \(stats.videosThisMonth)",
                        color: .blue
                    )

                    StatsCard(
                        title: "Species Identified",
                        value: "\(stats.speciesIdentified)",
                        subtitle: "Most recent: \(stats.mostRecentSpecies)",
                        color: .green
                    )

                    StatsCard(
                        title: "Knowledge Points",
                        value: "\(stats.knowledgePoints)",
                        subtitle: "Rank: #\(stats.globalRank) globally",
                        color: .orange
                    )

                    StatsCard(
                        title: "Validations Made",
                        value: "\(stats.validationsMade)",
                        subtitle: "Accuracy: \(stats.validationAccuracy, specifier: "%.1f")%",
                        color: .purple
                    )
                }
                .padding()
            }
            .navigationTitle("My Stats")
            .onAppear {
                loadUserStats()
            }
        }
    }

    private func loadUserStats() {
        // Load user statistics from API
        StatsAPI.shared.getUserStats { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let userStats):
                    self.stats = userStats
                case .failure(let error):
                    print("Failed to load stats: \(error)")
                }
            }
        }
    }
}

struct StatsCard: View {
    let title: String
    let value: String
    let subtitle: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
                .foregroundColor(.secondary)

            Text(value)
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(color)

            Text(subtitle)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

// Camera Manager for video recording
class CameraManager: NSObject, ObservableObject {
    @Published var isRecording = false

    private var captureSession: AVCaptureSession?
    private var movieOutput: AVCaptureMovieFileOutput?

    override init() {
        super.init()
        setupCamera()
    }

    private func setupCamera() {
        captureSession = AVCaptureSession()

        guard let captureSession = captureSession else { return }

        // Configure camera input
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: camera) else { return }

        if captureSession.canAddInput(input) {
            captureSession.addInput(input)
        }

        // Configure movie output
        movieOutput = AVCaptureMovieFileOutput()
        if let movieOutput = movieOutput, captureSession.canAddOutput(movieOutput) {
            captureSession.addOutput(movieOutput)
        }

        captureSession.startRunning()
    }

    func startRecording() {
        guard let movieOutput = movieOutput else { return }

        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let outputURL = documentsPath.appendingPathComponent("recording_\(Date().timeIntervalSince1970).mov")

        movieOutput.startRecording(to: outputURL, recordingDelegate: self)
        isRecording = true
    }

    func stopRecording() {
        movieOutput?.stopRecording()
        isRecording = false
    }
}

extension CameraManager: AVCaptureFileOutputRecordingDelegate {
    func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
        if let error = error {
            print("Recording error: \(error)")
        } else {
            // Upload recorded video
            VideoUploadService.shared.uploadVideo(url: outputFileURL)
        }
    }
}
```

------------------------------------------------------------------------

## 🚀 Deployment Strategy

### Kubernetes Deployment

``` yaml
# infrastructure/kubernetes/web-platform.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sharktrack-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sharktrack-web
  template:
    metadata:
      labels:
        app: sharktrack-web
    spec:
      containers:
      - name: web-app
        image: sharktrack/web-platform:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: sharktrack-web-service
spec:
  selector:
    app: sharktrack-web
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bittorrent-tracker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: bittorrent-tracker
  template:
    metadata:
      labels:
        app: bittorrent-tracker
    spec:
      containers:
      - name: tracker
        image: sharktrack/bittorrent-tracker:latest
        ports:
        - containerPort: 8000
        env:
        - name: TRACKER_ANNOUNCE_URL
          value: "https://tracker.sharktrack.org/announce"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blockchain-node
spec:
  replicas: 1
  selector:
    matchLabels:
      app: blockchain-node
  template:
    metadata:
      labels:
        app: blockchain-node
    spec:
      containers:
      - name: blockchain
        image: sharktrack/blockchain-node:latest
        ports:
        - containerPort: 5000
        volumeMounts:
        - name: blockchain-data
          mountPath: /data
      volumes:
      - name: blockchain-data
        persistentVolumeClaim:
          claimName: blockchain-pvc
```

### Infrastructure as Code (Terraform)

``` hcl
# infrastructure/terraform/main.tf
provider "aws" {
  region = "us-west-2"
}

# EKS Cluster for main application
resource "aws_eks_cluster" "sharktrack" {
  name     = "sharktrack-cluster"
  role_arn = aws_iam_role.cluster.arn

  vpc_config {
    subnet_ids = aws_subnet.sharktrack[*].id
  }

  depends_on = [
    aws_iam_role_policy_attachment.cluster_AmazonEKSClusterPolicy,
  ]
}

# RDS PostgreSQL for main database
resource "aws_db_instance" "sharktrack_db" {
  identifier = "sharktrack-postgres"

  engine         = "postgres"
  engine_version = "13.7"
  instance_class = "db.t3.medium"

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = "sharktrack"
  username = "sharktrack"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.sharktrack.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "sharktrack-final-snapshot"
}

# ElastiCache Redis for caching
resource "aws_elasticache_cluster" "sharktrack_redis" {
  cluster_id           = "sharktrack-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis6.x"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.sharktrack.name
  security_group_ids   = [aws_security_group.redis.id]
}

# S3 bucket for video storage
resource "aws_s3_bucket" "video_storage" {
  bucket = "sharktrack-videos-${random_string.bucket_suffix.result}"
}

resource "aws_s3_bucket_versioning" "video_storage" {
  bucket = aws_s3_bucket.video_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

# CloudFront distribution for global content delivery
resource "aws_cloudfront_distribution" "sharktrack_cdn" {
  origin {
    domain_name = aws_s3_bucket.video_storage.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.video_storage.id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.sharktrack.cloudfront_access_identity_path
    }
  }

  enabled             = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.video_storage.id}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
```

------------------------------------------------------------------------

## 📊 Monitoring and Analytics

### Real-time Dashboard

``` python
# monitoring/dashboard.py
from fastapi import FastAPI, WebSocket
import asyncio
import json
from datetime import datetime, timedelta
import redis
from sqlalchemy import create_engine, text

app = FastAPI()
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class PlatformMetrics:
    def __init__(self):
        self.db_engine = create_engine('postgresql://...')

    async def get_realtime_stats(self):
        """Get real-time platform statistics"""
        with self.db_engine.connect() as conn:
            # Videos processed today
            videos_today = conn.execute(text("""
                SELECT COUNT(*) FROM video_processing
                WHERE created_at >= CURRENT_DATE
            """)).scalar()

            # Active users in last hour
            active_users = conn.execute(text("""
                SELECT COUNT(DISTINCT user_id) FROM user_activity
                WHERE last_seen >= NOW() - INTERVAL '1 hour'
            """)).scalar()

            # Species detected this week
            species_week = conn.execute(text("""
                SELECT COUNT(DISTINCT species_id) FROM detections
                WHERE detected_at >= CURRENT_DATE - INTERVAL '7 days'
            """)).scalar()

            # Participating institutions
            institutions = conn.execute(text("""
                SELECT COUNT(DISTINCT institution_id) FROM users
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            """)).scalar()

        return {
            'videos_processed': videos_today,
            'active_researchers': active_users,
            'species_detected': species_week,
            'institutions': institutions,
            'timestamp': datetime.now().isoformat()
        }

@app.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    """WebSocket endpoint for real-time statistics"""
    await websocket.accept()
    metrics = PlatformMetrics()

    try:
        while True:
            stats = await metrics.get_realtime_stats()
            await websocket.send_text(json.dumps(stats))
            await asyncio.sleep(30)  # Update every 30 seconds
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/api/stats/live")
async def get_live_stats():
    """REST endpoint for current statistics"""
    metrics = PlatformMetrics()
    return await metrics.get_realtime_stats()
```

------------------------------------------------------------------------

This deployment architecture provides the complete infrastructure for transforming SharkTrack into a global marine research platform, with web portals, mobile apps, blockchain attribution, BitTorrent distribution, and real-time monitoring. The modular design allows for incremental deployment while maintaining the strategic vision of collective marine intelligence.
