# SharkTrack GitHub Pages Website Design

This document specifies the complete GitHub Pages website design with live statistics dashboard, webcam upload functionality, and platform integration.

## Website Architecture

### Technology Stack
- **Static Site Generator**: Jekyll with GitHub Pages
- **Frontend Framework**: Vanilla JavaScript with Web Components
- **CSS Framework**: Custom CSS Grid and Flexbox
- **Real-time Data**: WebSocket connections to platform API
- **Charts and Visualisation**: Chart.js and D3.js
- **Map Integration**: Leaflet.js for global network visualisation

### File Structure

```
docs/ (GitHub Pages root)
├── _config.yml                        # Jekyll configuration
├── index.html                         # Main landing page
├── _layouts/                           # Page templates
│   ├── default.html                    # Base layout template
│   ├── documentation.html              # Documentation layout
│   └── dashboard.html                  # Dashboard layout
├── _includes/                          # Reusable components
│   ├── header.html                     # Navigation header
│   ├── footer.html                     # Site footer
│   ├── stats-widget.html               # Statistics widget
│   └── upload-modal.html               # Upload modal component
├── assets/                             # Static assets
│   ├── css/
│   │   ├── main.scss                   # Main stylesheet
│   │   ├── components.scss             # Component styles
│   │   ├── dashboard.scss              # Dashboard-specific styles
│   │   └── responsive.scss             # Mobile responsiveness
│   ├── js/
│   │   ├── main.js                     # Core JavaScript
│   │   ├── dashboard.js                # Live dashboard functionality
│   │   ├── api-client.js               # Platform API integration
│   │   ├── upload-handler.js           # File upload management
│   │   ├── websocket-client.js         # Real-time data connection
│   │   └── components/                 # JavaScript components
│   │       ├── stats-counter.js        # Animated statistics
│   │       ├── world-map.js            # Global network map
│   │       ├── upload-widget.js        # Upload functionality
│   │       └── chart-manager.js        # Chart implementations
│   ├── images/
│   │   ├── logo.svg                    # SharkTrack logo
│   │   ├── hero-background.jpg         # Hero section image
│   │   ├── icons/                      # UI icons
│   │   └── screenshots/                # Platform screenshots
│   └── data/
│       ├── species.json                # Species reference data
│       ├── institutions.json           # Research institutions
│       └── sample-stats.json           # Fallback statistics
├── platform/                          # Platform documentation
│   ├── index.md                        # Platform overview
│   ├── getting-started.md              # Quick start guide
│   ├── api-reference.md                # API documentation
│   └── tutorials/                      # User tutorials
├── research/                           # Research section
│   ├── index.md                        # Research overview
│   ├── publications.md                 # Papers and publications
│   └── datasets.md                     # Available datasets
├── upload/                             # Upload portal
│   ├── index.html                      # Upload interface
│   ├── webcam.html                     # Webcam upload page
│   └── batch.html                      # Batch upload page
└── api/                                # API documentation
    ├── index.md                        # API overview
    ├── authentication.md               # Authentication guide
    └── endpoints/                      # Individual endpoints
        ├── videos.md
        ├── detections.md
        └── statistics.md
```

---

## Main Landing Page (`index.html`)

### Complete Implementation

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="SharkTrack - AI-powered global marine research platform for shark and ray detection">
    <meta property="og:title" content="SharkTrack - Global Marine Research Platform">
    <meta property="og:description" content="Collaborative AI platform for marine biodiversity research">
    <meta property="og:image" content="assets/images/hero-background.jpg">
    <title>SharkTrack - Global Marine Research Platform</title>

    <link rel="stylesheet" href="assets/css/main.css">
    <link rel="icon" type="image/svg+xml" href="assets/images/logo.svg">

    <!-- Chart.js for visualisations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Leaflet for maps -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
    <!-- Navigation Header -->
    <nav class="navbar" id="main-nav">
        <div class="nav-container">
            <div class="nav-brand">
                <img src="assets/images/logo.svg" alt="SharkTrack Logo" class="nav-logo">
                <span class="brand-text">SharkTrack</span>
                <span class="beta-badge">BETA</span>
            </div>

            <ul class="nav-links">
                <li><a href="#dashboard" class="nav-link">Dashboard</a></li>
                <li><a href="#features" class="nav-link">Features</a></li>
                <li><a href="platform/" class="nav-link">Platform</a></li>
                <li><a href="research/" class="nav-link">Research</a></li>
                <li><a href="api/" class="nav-link">API</a></li>
                <li><a href="#upload" class="nav-link upload-btn">Upload Data</a></li>
            </ul>

            <button class="mobile-menu-toggle" aria-label="Toggle navigation">
                <span></span>
                <span></span>
                <span></span>
            </button>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero" id="hero">
        <div class="hero-background">
            <video autoplay muted loop class="hero-video">
                <source src="assets/videos/underwater-sharks.mp4" type="video/mp4">
            </video>
            <div class="hero-overlay"></div>
        </div>

        <div class="hero-content">
            <h1 class="hero-title">
                Global Marine Research Platform
                <span class="title-highlight">Powered by AI</span>
            </h1>

            <p class="hero-subtitle">
                Collaborative platform for detecting, tracking, and studying sharks and rays
                through advanced computer vision and distributed research networks
            </p>

            <!-- Live Statistics Counter -->
            <div class="hero-stats" id="hero-stats">
                <div class="stat-card" data-stat="videos">
                    <span class="stat-number" id="videos-processed">0</span>
                    <span class="stat-label">Videos Processed</span>
                    <span class="stat-change positive" id="videos-change">+0</span>
                </div>

                <div class="stat-card" data-stat="species">
                    <span class="stat-number" id="species-detected">0</span>
                    <span class="stat-label">Species Detected</span>
                    <span class="stat-change positive" id="species-change">+0</span>
                </div>

                <div class="stat-card" data-stat="institutions">
                    <span class="stat-number" id="institutions-count">0</span>
                    <span class="stat-label">Research Institutions</span>
                    <span class="stat-change positive" id="institutions-change">+0</span>
                </div>

                <div class="stat-card" data-stat="data">
                    <span class="stat-number" id="data-shared">0</span>
                    <span class="stat-unit">TB</span>
                    <span class="stat-label">Data Shared</span>
                    <span class="stat-change positive" id="data-change">+0</span>
                </div>
            </div>

            <!-- Call to Action -->
            <div class="hero-actions">
                <button class="btn btn-primary" onclick="openUploadModal()">
                    Start Contributing
                </button>
                <button class="btn btn-secondary" onclick="scrollToSection('dashboard')">
                    View Live Dashboard
                </button>
            </div>
        </div>

        <!-- Scroll Indicator -->
        <div class="scroll-indicator">
            <div class="scroll-arrow"></div>
        </div>
    </section>

    <!-- Live Dashboard Section -->
    <section class="dashboard-section" id="dashboard">
        <div class="container">
            <header class="section-header">
                <h2>Live Platform Dashboard</h2>
                <p>Real-time statistics from the global SharkTrack network</p>
                <div class="status-indicator">
                    <span class="status-dot online"></span>
                    <span class="status-text">All systems operational</span>
                    <span class="last-update">Last updated: <span id="last-update-time">Just now</span></span>
                </div>
            </header>

            <div class="dashboard-grid">
                <!-- Processing Activity -->
                <div class="dashboard-card processing-card">
                    <div class="card-header">
                        <h3>Processing Activity</h3>
                        <div class="card-controls">
                            <button class="time-filter active" data-period="1h">1H</button>
                            <button class="time-filter" data-period="24h">24H</button>
                            <button class="time-filter" data-period="7d">7D</button>
                        </div>
                    </div>

                    <div class="card-content">
                        <canvas id="processing-chart" class="chart-canvas"></canvas>

                        <div class="card-stats">
                            <div class="stat-item">
                                <span class="stat-label">Active Jobs</span>
                                <span class="stat-value" id="active-jobs">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Queue Length</span>
                                <span class="stat-value" id="queue-length">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Avg. Processing Time</span>
                                <span class="stat-value" id="avg-processing-time">0s</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Global Network Map -->
                <div class="dashboard-card network-card">
                    <div class="card-header">
                        <h3>Global Research Network</h3>
                        <div class="network-legend">
                            <span class="legend-item">
                                <span class="legend-dot active"></span>
                                Active Nodes
                            </span>
                            <span class="legend-item">
                                <span class="legend-dot processing"></span>
                                Processing
                            </span>
                        </div>
                    </div>

                    <div class="card-content">
                        <div id="world-map" class="world-map"></div>

                        <div class="card-stats">
                            <div class="stat-item">
                                <span class="stat-label">Online Nodes</span>
                                <span class="stat-value" id="online-nodes">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">P2P Connections</span>
                                <span class="stat-value" id="p2p-connections">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Network Health</span>
                                <span class="stat-value health-good" id="network-health">98%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Discoveries -->
                <div class="dashboard-card discoveries-card">
                    <div class="card-header">
                        <h3>Recent Discoveries</h3>
                        <a href="research/discoveries.html" class="view-all-link">View All</a>
                    </div>

                    <div class="card-content">
                        <div class="discovery-timeline" id="recent-discoveries">
                            <!-- Dynamically populated -->
                        </div>

                        <div class="card-stats">
                            <div class="stat-item">
                                <span class="stat-label">This Month</span>
                                <span class="stat-value" id="monthly-discoveries">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">This Year</span>
                                <span class="stat-value" id="yearly-discoveries">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Total Species</span>
                                <span class="stat-value" id="total-species">0</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Collaboration Activity -->
                <div class="dashboard-card collaboration-card">
                    <div class="card-header">
                        <h3>Collaboration Activity</h3>
                        <div class="activity-indicator">
                            <span class="activity-pulse"></span>
                            <span>Live Activity</span>
                        </div>
                    </div>

                    <div class="card-content">
                        <canvas id="collaboration-chart" class="chart-canvas"></canvas>

                        <div class="card-stats">
                            <div class="stat-item">
                                <span class="stat-label">Active Reviewers</span>
                                <span class="stat-value" id="active-reviewers">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Annotations Today</span>
                                <span class="stat-value" id="daily-annotations">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Validation Accuracy</span>
                                <span class="stat-value" id="validation-accuracy">0%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Platform Features -->
    <section class="features-section" id="features">
        <div class="container">
            <header class="section-header">
                <h2>Platform Capabilities</h2>
                <p>Comprehensive tools for marine research and collaboration</p>
            </header>

            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <svg class="icon-ai"><!-- AI icon SVG --></svg>
                    </div>
                    <h3>AI Detection Engine</h3>
                    <p>YOLOv8-powered detection with 89% accuracy for elasmobranchs</p>
                    <ul class="feature-list">
                        <li>Real-time object detection</li>
                        <li>Multi-species tracking</li>
                        <li>MaxN computation</li>
                    </ul>
                    <a href="platform/detection.html" class="feature-link">Learn More</a>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <svg class="icon-collaborate"><!-- Collaboration icon SVG --></svg>
                    </div>
                    <h3>Collaborative Review</h3>
                    <p>Global annotation platform with gamification and real-time validation</p>
                    <ul class="feature-list">
                        <li>Interactive annotation tools</li>
                        <li>Peer review system</li>
                        <li>Achievement tracking</li>
                    </ul>
                    <a href="platform/collaboration.html" class="feature-link">Join Platform</a>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <svg class="icon-network"><!-- Network icon SVG --></svg>
                    </div>
                    <h3>Distributed Network</h3>
                    <p>BitTorrent-based video sharing with federated research data</p>
                    <ul class="feature-list">
                        <li>P2P data sharing</li>
                        <li>Decentralised storage</li>
                        <li>Global accessibility</li>
                    </ul>
                    <a href="platform/network.html" class="feature-link">Explore Network</a>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <svg class="icon-blockchain"><!-- Blockchain icon SVG --></svg>
                    </div>
                    <h3>Knowledge Attribution</h3>
                    <p>Blockchain-based contribution tracking and species intelligence</p>
                    <ul class="feature-list">
                        <li>Proof-of-Science consensus</li>
                        <li>Contribution rewards</li>
                        <li>Immutable knowledge</li>
                    </ul>
                    <a href="platform/blockchain.html" class="feature-link">Learn System</a>
                </div>
            </div>
        </div>
    </section>

    <!-- Data Upload Portal -->
    <section class="upload-section" id="upload">
        <div class="container">
            <header class="section-header">
                <h2>Contribute Research Data</h2>
                <p>Upload your marine video data and join the global research effort</p>
            </header>

            <div class="upload-grid">
                <div class="upload-card webcam-upload">
                    <div class="upload-icon">
                        <svg class="icon-camera"><!-- Camera icon SVG --></svg>
                    </div>
                    <h3>Webcam Upload</h3>
                    <p>Direct upload from underwater cameras with GPS metadata</p>

                    <div class="upload-features">
                        <span class="feature-tag">Real-time upload</span>
                        <span class="feature-tag">GPS integration</span>
                        <span class="feature-tag">Metadata extraction</span>
                    </div>

                    <button class="btn btn-primary" onclick="openWebcamUpload()">
                        Start Camera Upload
                    </button>
                </div>

                <div class="upload-card batch-upload">
                    <div class="upload-icon">
                        <svg class="icon-batch"><!-- Batch icon SVG --></svg>
                    </div>
                    <h3>Batch Processing</h3>
                    <p>Large dataset upload with automated processing and analysis</p>

                    <div class="upload-features">
                        <span class="feature-tag">Multi-file support</span>
                        <span class="feature-tag">Progress tracking</span>
                        <span class="feature-tag">Auto-processing</span>
                    </div>

                    <button class="btn btn-primary" onclick="openBatchUpload()">
                        Upload Dataset
                    </button>
                </div>

                <div class="upload-card mobile-upload">
                    <div class="upload-icon">
                        <svg class="icon-mobile"><!-- Mobile icon SVG --></svg>
                    </div>
                    <h3>Mobile Apps</h3>
                    <p>Upload via Android and iOS applications with field recording</p>

                    <div class="app-downloads">
                        <a href="#android-app" class="app-link android">
                            <img src="assets/images/google-play-badge.png" alt="Get it on Google Play">
                        </a>
                        <a href="#ios-app" class="app-link ios">
                            <img src="assets/images/app-store-badge.png" alt="Download on App Store">
                        </a>
                    </div>
                </div>
            </div>

            <!-- Upload Progress Indicator -->
            <div class="upload-status" id="upload-status" style="display: none;">
                <div class="status-header">
                    <h4>Upload in Progress</h4>
                    <button class="close-status" onclick="hideUploadStatus()">&times;</button>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="upload-progress"></div>
                </div>
                <div class="status-details">
                    <span id="upload-filename">filename.mp4</span>
                    <span id="upload-percentage">0%</span>
                </div>
            </div>
        </div>
    </section>

    <!-- Research Highlights -->
    <section class="research-section" id="research">
        <div class="container">
            <header class="section-header">
                <h2>Research Impact</h2>
                <p>Scientific discoveries enabled by the SharkTrack platform</p>
            </header>

            <div class="research-grid">
                <div class="research-card featured">
                    <div class="research-image">
                        <img src="assets/images/research/tiger-shark-study.jpg" alt="Tiger Shark Research">
                        <div class="research-badge">Latest Publication</div>
                    </div>
                    <div class="research-content">
                        <h3>Tiger Shark Migration Patterns in the Indo-Pacific</h3>
                        <p class="research-authors">Dr. Sarah Chen, Marine Institute & Global Research Network</p>
                        <p class="research-summary">
                            Large-scale analysis of tiger shark movements using collaborative
                            video data from 47 research institutions across the Indo-Pacific region.
                        </p>
                        <div class="research-stats">
                            <span>2,847 hours of video analysed</span>
                            <span>1,203 individual sharks tracked</span>
                            <span>New migration route discovered</span>
                        </div>
                        <a href="research/publications/tiger-shark-2024.html" class="research-link">
                            Read Full Paper
                        </a>
                    </div>
                </div>

                <div class="impact-metrics">
                    <h3>Platform Impact Metrics</h3>
                    <div class="metrics-grid">
                        <div class="metric-item">
                            <span class="metric-number">156</span>
                            <span class="metric-label">Research Papers</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-number">23,000+</span>
                            <span class="metric-label">Hours Analysed</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-number">89</span>
                            <span class="metric-label">Institutions</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-number">47</span>
                            <span class="metric-label">Countries</span>
                        </div>
                    </div>

                    <div class="recent-papers">
                        <h4>Recent Publications</h4>
                        <ul class="papers-list">
                            <li>
                                <a href="research/publications/reef-shark-behaviour-2024.html">
                                    Reef Shark Behaviour Analysis Using Automated Video Processing
                                </a>
                                <span class="paper-date">March 2024</span>
                            </li>
                            <li>
                                <a href="research/publications/climate-impact-2024.html">
                                    Climate Change Impact on Elasmobranch Distribution
                                </a>
                                <span class="paper-date">February 2024</span>
                            </li>
                            <li>
                                <a href="research/publications/ai-accuracy-2024.html">
                                    AI-Powered Marine Life Detection: Accuracy and Validation
                                </a>
                                <span class="paper-date">January 2024</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h4>Platform</h4>
                    <ul>
                        <li><a href="platform/">Overview</a></li>
                        <li><a href="platform/getting-started.html">Getting Started</a></li>
                        <li><a href="api/">API Documentation</a></li>
                        <li><a href="platform/status.html">System Status</a></li>
                    </ul>
                </div>

                <div class="footer-section">
                    <h4>Research</h4>
                    <ul>
                        <li><a href="research/">Publications</a></li>
                        <li><a href="research/datasets.html">Datasets</a></li>
                        <li><a href="research/collaborations.html">Collaborations</a></li>
                        <li><a href="research/funding.html">Funding</a></li>
                    </ul>
                </div>

                <div class="footer-section">
                    <h4>Community</h4>
                    <ul>
                        <li><a href="https://github.com/username/sharktrack-platform">GitHub</a></li>
                        <li><a href="community/forum.html">Discussion Forum</a></li>
                        <li><a href="community/events.html">Events</a></li>
                        <li><a href="community/newsletter.html">Newsletter</a></li>
                    </ul>
                </div>

                <div class="footer-section">
                    <h4>Support</h4>
                    <ul>
                        <li><a href="support/">Help Centre</a></li>
                        <li><a href="support/contact.html">Contact</a></li>
                        <li><a href="support/privacy.html">Privacy Policy</a></li>
                        <li><a href="support/terms.html">Terms of Service</a></li>
                    </ul>
                </div>
            </div>

            <div class="footer-bottom">
                <div class="footer-brand">
                    <img src="assets/images/logo.svg" alt="SharkTrack">
                    <span>SharkTrack</span>
                </div>

                <div class="footer-legal">
                    <span>&copy; 2024 SharkTrack Platform. GPL-3.0 License.</span>
                    <span>Transforming marine biology through collaborative AI.</span>
                </div>

                <div class="footer-social">
                    <a href="https://twitter.com/sharktrack" aria-label="Twitter">
                        <svg class="social-icon"><!-- Twitter icon --></svg>
                    </a>
                    <a href="https://linkedin.com/company/sharktrack" aria-label="LinkedIn">
                        <svg class="social-icon"><!-- LinkedIn icon --></svg>
                    </a>
                    <a href="https://youtube.com/sharktrack" aria-label="YouTube">
                        <svg class="social-icon"><!-- YouTube icon --></svg>
                    </a>
                </div>
            </div>
        </div>
    </footer>

    <!-- Upload Modal -->
    <div class="modal" id="upload-modal" style="display: none;">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Upload Research Data</h3>
                <button class="modal-close" onclick="closeUploadModal()">&times;</button>
            </div>

            <div class="modal-body">
                <div class="upload-options">
                    <button class="upload-option" onclick="selectUploadType('webcam')">
                        <svg class="option-icon"><!-- Camera icon --></svg>
                        <span>Webcam Upload</span>
                    </button>

                    <button class="upload-option" onclick="selectUploadType('file')">
                        <svg class="option-icon"><!-- File icon --></svg>
                        <span>File Upload</span>
                    </button>

                    <button class="upload-option" onclick="selectUploadType('batch')">
                        <svg class="option-icon"><!-- Batch icon --></svg>
                        <span>Batch Upload</span>
                    </button>
                </div>

                <div class="upload-form" id="upload-form" style="display: none;">
                    <!-- Dynamic upload form content -->
                </div>
            </div>
        </div>
    </div>

    <!-- JavaScript Includes -->
    <script src="assets/js/main.js"></script>
    <script src="assets/js/dashboard.js"></script>
    <script src="assets/js/api-client.js"></script>
    <script src="assets/js/upload-handler.js"></script>
    <script src="assets/js/websocket-client.js"></script>

    <!-- Component Scripts -->
    <script src="assets/js/components/stats-counter.js"></script>
    <script src="assets/js/components/world-map.js"></script>
    <script src="assets/js/components/chart-manager.js"></script>
    <script src="assets/js/components/upload-widget.js"></script>
</body>
</html>
```

---

## JavaScript Implementation

### Main Dashboard Script (`assets/js/dashboard.js`)

```javascript
class SharkTrackDashboard {
    constructor() {
        this.apiClient = new APIClient();
        this.websocketClient = new WebSocketClient();
        this.chartManager = new ChartManager();
        this.statsCounter = new StatsCounter();
        this.worldMap = new WorldMap();

        this.init();
    }

    async init() {
        // Initialize components
        await this.initializeComponents();

        // Start real-time updates
        this.startRealTimeUpdates();

        // Initialize event listeners
        this.setupEventListeners();

        // Load initial data
        await this.loadInitialData();
    }

    async initializeComponents() {
        // Initialize charts
        this.processingChart = this.chartManager.createProcessingChart('processing-chart');
        this.collaborationChart = this.chartManager.createCollaborationChart('collaboration-chart');

        // Initialize world map
        this.worldMap.initialize('world-map');

        // Initialize stats counters
        this.statsCounter.initialize([
            'videos-processed',
            'species-detected',
            'institutions-count',
            'data-shared'
        ]);
    }

    startRealTimeUpdates() {
        // WebSocket connection for real-time data
        this.websocketClient.connect('wss://api.sharktrack.org/ws/dashboard');

        this.websocketClient.on('stats-update', (data) => {
            this.updateStatistics(data);
        });

        this.websocketClient.on('processing-update', (data) => {
            this.updateProcessingChart(data);
        });

        this.websocketClient.on('network-update', (data) => {
            this.updateNetworkMap(data);
        });

        this.websocketClient.on('discovery-update', (data) => {
            this.updateDiscoveries(data);
        });

        // Fallback polling if WebSocket fails
        setInterval(() => {
            if (!this.websocketClient.isConnected()) {
                this.fetchLatestData();
            }
        }, 30000); // 30 second intervals
    }

    setupEventListeners() {
        // Time filter buttons
        document.querySelectorAll('.time-filter').forEach(button => {
            button.addEventListener('click', (e) => {
                this.handleTimeFilterChange(e.target.dataset.period);
            });
        });

        // Navigation smooth scrolling
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                if (link.getAttribute('href').startsWith('#')) {
                    e.preventDefault();
                    this.smoothScrollTo(link.getAttribute('href'));
                }
            });
        });

        // Mobile menu toggle
        const mobileToggle = document.querySelector('.mobile-menu-toggle');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', () => {
                this.toggleMobileMenu();
            });
        }
    }

    async loadInitialData() {
        try {
            // Load statistics
            const stats = await this.apiClient.getStatistics();
            this.updateStatistics(stats);

            // Load processing data
            const processingData = await this.apiClient.getProcessingData('24h');
            this.updateProcessingChart(processingData);

            // Load network data
            const networkData = await this.apiClient.getNetworkData();
            this.updateNetworkMap(networkData);

            // Load recent discoveries
            const discoveries = await this.apiClient.getRecentDiscoveries();
            this.updateDiscoveries(discoveries);

            // Load collaboration data
            const collaborationData = await this.apiClient.getCollaborationData();
            this.updateCollaborationChart(collaborationData);

        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showErrorMessage('Failed to load dashboard data');
        }
    }

    updateStatistics(data) {
        // Animate counter updates
        this.statsCounter.animateUpdate('videos-processed', data.videosProcessed);
        this.statsCounter.animateUpdate('species-detected', data.speciesDetected);
        this.statsCounter.animateUpdate('institutions-count', data.institutionsCount);
        this.statsCounter.animateUpdate('data-shared', data.dataSharedTB);

        // Update change indicators
        this.updateChangeIndicators(data.changes);

        // Update additional stats
        document.getElementById('active-jobs').textContent = data.activeJobs;
        document.getElementById('queue-length').textContent = data.queueLength;
        document.getElementById('online-nodes').textContent = data.onlineNodes;
        document.getElementById('p2p-connections').textContent = data.p2pConnections;
        document.getElementById('active-reviewers').textContent = data.activeReviewers;
        document.getElementById('daily-annotations').textContent = data.dailyAnnotations;
    }

    updateChangeIndicators(changes) {
        Object.entries(changes).forEach(([key, value]) => {
            const element = document.getElementById(`${key}-change`);
            if (element) {
                element.textContent = value > 0 ? `+${value}` : value.toString();
                element.className = `stat-change ${value >= 0 ? 'positive' : 'negative'}`;
            }
        });
    }

    updateProcessingChart(data) {
        this.processingChart.data.labels = data.labels;
        this.processingChart.data.datasets[0].data = data.processingRate;
        this.processingChart.data.datasets[1].data = data.completionRate;
        this.processingChart.update('none');
    }

    updateCollaborationChart(data) {
        this.collaborationChart.data.labels = data.labels;
        this.collaborationChart.data.datasets[0].data = data.annotations;
        this.collaborationChart.data.datasets[1].data = data.validations;
        this.collaborationChart.update('none');
    }

    updateNetworkMap(data) {
        this.worldMap.updateNodes(data.nodes);
        this.worldMap.updateConnections(data.connections);

        // Update network health indicator
        const healthElement = document.getElementById('network-health');
        if (healthElement) {
            healthElement.textContent = `${data.health}%`;
            healthElement.className = `stat-value ${this.getHealthClass(data.health)}`;
        }
    }

    updateDiscoveries(discoveries) {
        const container = document.getElementById('recent-discoveries');
        container.innerHTML = '';

        discoveries.forEach(discovery => {
            const discoveryElement = this.createDiscoveryElement(discovery);
            container.appendChild(discoveryElement);
        });

        // Update discovery counters
        document.getElementById('monthly-discoveries').textContent = discoveries.monthlyCount;
        document.getElementById('yearly-discoveries').textContent = discoveries.yearlyCount;
        document.getElementById('total-species').textContent = discoveries.totalSpecies;
    }

    createDiscoveryElement(discovery) {
        const element = document.createElement('div');
        element.className = 'discovery-item';
        element.innerHTML = `
            <div class="discovery-image">
                <img src="${discovery.image}" alt="${discovery.species}">
            </div>
            <div class="discovery-content">
                <h4>${discovery.species}</h4>
                <p>${discovery.location}</p>
                <span class="discovery-date">${discovery.date}</span>
            </div>
        `;
        return element;
    }

    handleTimeFilterChange(period) {
        // Update active filter
        document.querySelectorAll('.time-filter').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-period="${period}"]`).classList.add('active');

        // Fetch new data for the selected period
        this.fetchProcessingData(period);
    }

    async fetchProcessingData(period) {
        try {
            const data = await this.apiClient.getProcessingData(period);
            this.updateProcessingChart(data);
        } catch (error) {
            console.error('Failed to fetch processing data:', error);
        }
    }

    getHealthClass(health) {
        if (health >= 95) return 'health-excellent';
        if (health >= 90) return 'health-good';
        if (health >= 80) return 'health-fair';
        return 'health-poor';
    }

    smoothScrollTo(target) {
        const element = document.querySelector(target);
        if (element) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }

    toggleMobileMenu() {
        const nav = document.querySelector('.navbar');
        nav.classList.toggle('mobile-open');
    }

    showErrorMessage(message) {
        // Create or update error notification
        const notification = document.querySelector('.error-notification') ||
                           this.createErrorNotification();
        notification.textContent = message;
        notification.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.style.display = 'none';
        }, 5000);
    }

    createErrorNotification() {
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        document.body.appendChild(notification);
        return notification;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.sharkTrackDashboard = new SharkTrackDashboard();
});
```

### WebSocket Client (`assets/js/websocket-client.js`)

```javascript
class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.listeners = new Map();
    }

    connect(url) {
        try {
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.emit('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.emit(data.type, data.payload);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.emit('disconnected');
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

            setTimeout(() => {
                this.connect(this.ws.url);
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    emit(event, data) {
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            callbacks.forEach(callback => callback(data));
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    send(message) {
        if (this.isConnected()) {
            this.ws.send(JSON.stringify(message));
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}
```

---

## CSS Styling (`assets/css/main.scss`)

```scss
// Variables
:root {
  --primary-color: #1e40af;
  --secondary-color: #0ea5e9;
  --accent-color: #f59e0b;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;

  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-dark: #0f172a;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-light: #94a3b8;

  --border-color: #e2e8f0;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);

  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  --header-height: 4rem;
  --container-max-width: 1200px;
  --border-radius: 0.5rem;
  --transition: all 0.3s ease;
}

// Base styles
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  font-family: var(--font-family);
  line-height: 1.6;
  color: var(--text-primary);
  background-color: var(--bg-primary);
}

.container {
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: 0 1rem;
}

// Navigation
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  z-index: 1000;
  height: var(--header-height);

  .nav-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 100%;
    max-width: var(--container-max-width);
    margin: 0 auto;
    padding: 0 1rem;
  }

  .nav-brand {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    font-size: 1.25rem;

    .nav-logo {
      height: 2rem;
      width: auto;
    }

    .beta-badge {
      background: var(--accent-color);
      color: white;
      font-size: 0.75rem;
      padding: 0.125rem 0.375rem;
      border-radius: 9999px;
      font-weight: 500;
    }
  }

  .nav-links {
    display: flex;
    list-style: none;
    gap: 2rem;
    align-items: center;

    .nav-link {
      text-decoration: none;
      color: var(--text-primary);
      font-weight: 500;
      transition: var(--transition);

      &:hover {
        color: var(--primary-color);
      }

      &.upload-btn {
        background: var(--primary-color);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: var(--border-radius);

        &:hover {
          background: var(--secondary-color);
          color: white;
        }
      }
    }
  }

  .mobile-menu-toggle {
    display: none;
    flex-direction: column;
    gap: 0.25rem;
    background: none;
    border: none;
    cursor: pointer;

    span {
      width: 1.5rem;
      height: 2px;
      background: var(--text-primary);
      transition: var(--transition);
    }
  }
}

// Hero section
.hero {
  position: relative;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  .hero-background {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    .hero-video {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .hero-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(
        45deg,
        rgba(30, 64, 175, 0.8),
        rgba(14, 165, 233, 0.6)
      );
    }
  }

  .hero-content {
    position: relative;
    z-index: 10;
    text-align: center;
    color: white;
    max-width: 800px;
    padding: 0 1rem;

    .hero-title {
      font-size: clamp(2.5rem, 5vw, 4rem);
      font-weight: 800;
      margin-bottom: 1rem;
      line-height: 1.2;

      .title-highlight {
        background: linear-gradient(135deg, #f59e0b, #ea580c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }

    .hero-subtitle {
      font-size: 1.25rem;
      margin-bottom: 3rem;
      opacity: 0.9;
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
    }
  }

  .hero-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;

    .stat-card {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: var(--border-radius);
      padding: 1.5rem;
      text-align: center;
      backdrop-filter: blur(10px);
      transition: var(--transition);

      &:hover {
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.15);
      }

      .stat-number {
        display: block;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
      }

      .stat-unit {
        font-size: 1.5rem;
        font-weight: 600;
        opacity: 0.8;
      }

      .stat-label {
        display: block;
        font-size: 0.875rem;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
      }

      .stat-change {
        font-size: 0.75rem;
        padding: 0.125rem 0.375rem;
        border-radius: 9999px;

        &.positive {
          background: rgba(16, 185, 129, 0.2);
          color: #10b981;
        }

        &.negative {
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
        }
      }
    }
  }

  .hero-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  .scroll-indicator {
    position: absolute;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    animation: bounce 2s infinite;

    .scroll-arrow {
      width: 24px;
      height: 24px;
      border-right: 2px solid white;
      border-bottom: 2px solid white;
      transform: rotate(45deg);
    }
  }
}

// Buttons
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: var(--border-radius);
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: var(--transition);
  font-size: 1rem;

  &.btn-primary {
    background: var(--primary-color);
    color: white;

    &:hover {
      background: var(--secondary-color);
      transform: translateY(-1px);
      box-shadow: var(--shadow-md);
    }
  }

  &.btn-secondary {
    background: transparent;
    color: white;
    border: 2px solid rgba(255, 255, 255, 0.5);

    &:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: white;
    }
  }
}

// Dashboard section
.dashboard-section {
  padding: 5rem 0;
  background: var(--bg-secondary);

  .section-header {
    text-align: center;
    margin-bottom: 3rem;

    h2 {
      font-size: 2.5rem;
      font-weight: 800;
      margin-bottom: 1rem;
      color: var(--text-primary);
    }

    p {
      font-size: 1.125rem;
      color: var(--text-secondary);
      max-width: 600px;
      margin: 0 auto 2rem;
    }

    .status-indicator {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      color: var(--text-light);

      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;

        &.online {
          background: var(--success-color);
          animation: pulse 2s infinite;
        }
      }
    }
  }

  .dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
  }

  .dashboard-card {
    background: white;
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-color);
    transition: var(--transition);

    &:hover {
      box-shadow: var(--shadow-md);
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.5rem;

      h3 {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
      }

      .card-controls {
        display: flex;
        gap: 0.25rem;

        .time-filter {
          padding: 0.25rem 0.75rem;
          border: 1px solid var(--border-color);
          background: white;
          border-radius: 0.25rem;
          cursor: pointer;
          font-size: 0.875rem;
          transition: var(--transition);

          &.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
          }

          &:hover:not(.active) {
            background: var(--bg-secondary);
          }
        }
      }
    }

    .card-content {
      .chart-canvas {
        width: 100%;
        height: 200px;
        margin-bottom: 1rem;
      }

      .world-map {
        width: 100%;
        height: 250px;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
      }
    }

    .card-stats {
      display: flex;
      justify-content: space-between;
      padding-top: 1rem;
      border-top: 1px solid var(--border-color);

      .stat-item {
        text-align: center;

        .stat-label {
          display: block;
          font-size: 0.75rem;
          color: var(--text-light);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 0.25rem;
        }

        .stat-value {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-primary);

          &.health-excellent {
            color: var(--success-color);
          }

          &.health-good {
            color: var(--success-color);
          }

          &.health-fair {
            color: var(--warning-color);
          }

          &.health-poor {
            color: var(--error-color);
          }
        }
      }
    }
  }
}

// Upload section
.upload-section {
  padding: 5rem 0;
  background: white;

  .upload-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
  }

  .upload-card {
    background: var(--bg-secondary);
    border-radius: var(--border-radius);
    padding: 2rem;
    text-align: center;
    border: 2px solid transparent;
    transition: var(--transition);

    &:hover {
      border-color: var(--primary-color);
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
    }

    .upload-icon {
      width: 4rem;
      height: 4rem;
      margin: 0 auto 1.5rem;
      background: var(--primary-color);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;

      svg {
        width: 2rem;
        height: 2rem;
        fill: white;
      }
    }

    h3 {
      font-size: 1.5rem;
      font-weight: 700;
      margin-bottom: 1rem;
      color: var(--text-primary);
    }

    p {
      color: var(--text-secondary);
      margin-bottom: 1.5rem;
    }

    .upload-features {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      justify-content: center;
      margin-bottom: 1.5rem;

      .feature-tag {
        background: var(--primary-color);
        color: white;
        font-size: 0.75rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 500;
      }
    }

    .app-downloads {
      display: flex;
      gap: 1rem;
      justify-content: center;

      .app-link img {
        height: 3rem;
        width: auto;
      }
    }
  }

  .upload-status {
    background: white;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow-md);

    .status-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;

      h4 {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
      }

      .close-status {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: var(--text-light);

        &:hover {
          color: var(--text-primary);
        }
      }
    }

    .progress-bar {
      width: 100%;
      height: 0.5rem;
      background: var(--bg-secondary);
      border-radius: 9999px;
      overflow: hidden;
      margin-bottom: 1rem;

      .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        transition: width 0.3s ease;
        width: 0%;
      }
    }

    .status-details {
      display: flex;
      justify-content: space-between;
      font-size: 0.875rem;
      color: var(--text-secondary);
    }
  }
}

// Modal
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;

  .modal-content {
    background: white;
    border-radius: var(--border-radius);
    max-width: 600px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.5rem;
      border-bottom: 1px solid var(--border-color);

      h3 {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
      }

      .modal-close {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: var(--text-light);

        &:hover {
          color: var(--text-primary);
        }
      }
    }

    .modal-body {
      padding: 1.5rem;

      .upload-options {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;

        .upload-option {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.75rem;
          padding: 1.5rem;
          border: 2px solid var(--border-color);
          border-radius: var(--border-radius);
          background: white;
          cursor: pointer;
          transition: var(--transition);

          &:hover {
            border-color: var(--primary-color);
            background: var(--bg-secondary);
          }

          .option-icon {
            width: 2rem;
            height: 2rem;
            fill: var(--primary-color);
          }

          span {
            font-weight: 600;
            color: var(--text-primary);
          }
        }
      }
    }
  }
}

// Animations
@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0) translateX(-50%);
  }
  40% {
    transform: translateY(-10px) translateX(-50%);
  }
  60% {
    transform: translateY(-5px) translateX(-50%);
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
  }
}

// Responsive design
@media (max-width: 768px) {
  .navbar {
    .nav-links {
      display: none;
    }

    .mobile-menu-toggle {
      display: flex;
    }

    &.mobile-open {
      .nav-links {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border-top: 1px solid var(--border-color);
        flex-direction: column;
        padding: 1rem 0;
        display: flex;
      }
    }
  }

  .hero {
    .hero-stats {
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }

    .hero-actions {
      flex-direction: column;
      align-items: center;
    }
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .upload-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .hero {
    .hero-stats {
      grid-template-columns: 1fr;
    }
  }

  .dashboard-card {
    .card-stats {
      flex-direction: column;
      gap: 0.75rem;
    }
  }
}
```

---

## Jekyll Configuration (`_config.yml`)

```yaml
# Site settings
title: "SharkTrack - Global Marine Research Platform"
description: "AI-powered collaborative platform for marine biodiversity research"
url: "https://username.github.io"
baseurl: "/sharktrack-platform"

# Author information
author:
  name: "SharkTrack Team"
  email: "team@sharktrack.org"

# Build settings
markdown: kramdown
highlighter: rouge
plugins:
  - jekyll-feed
  - jekyll-sitemap
  - jekyll-seo-tag

# Collections
collections:
  tutorials:
    output: true
    permalink: /:collection/:name/
  research:
    output: true
    permalink: /:collection/:name/

# Sass configuration
sass:
  sass_dir: assets/css
  style: compressed

# Exclude from processing
exclude:
  - Gemfile
  - Gemfile.lock
  - node_modules
  - vendor
  - README.md

# Include files
include:
  - _headers
  - _redirects

# Default layouts
defaults:
  - scope:
      path: ""
      type: "pages"
    values:
      layout: "default"
  - scope:
      path: ""
      type: "tutorials"
    values:
      layout: "documentation"
  - scope:
      path: ""
      type: "research"
    values:
      layout: "research"

# SEO settings
twitter:
  username: sharktrack
  card: summary_large_image

facebook:
  app_id: 1234567890
  publisher: https://www.facebook.com/sharktrack

logo: /assets/images/logo.png

# Analytics
google_analytics: UA-XXXXXXXXX-X

# Performance settings
compress_html:
  clippings: all
  comments: all
  endings: all
  startings: [html, head, body]
```

---

## Interlinked Documentation Strategy

### Automated Documentation Generation

**Migration from Local Markdown Structure**:
```bash
# Automated migration script
scripts/migrate-docs.sh
├── Parse existing docs/ structure
├── Generate Jekyll front matter
├── Create navigation hierarchies
├── Update cross-references
└── Deploy to GitHub Pages
```

**Source Integration**:
- **Existing Structure**: Current `docs/` folder with 5 themed subdirectories
- **Jekyll Collections**: Automatic conversion to Jekyll collections
- **Cross-References**: Automated link validation and updating
- **Live Updates**: GitHub Actions trigger rebuilds on doc changes

### Documentation Architecture

**Collection Mapping**:
```yaml
collections:
  core_system:
    source: "01-core-system/"
    output: true
    permalink: /core/:name/
  platform_vision:
    source: "02-platform-vision/"
    output: true
    permalink: /platform/:name/
  infrastructure:
    source: "03-infrastructure/"
    output: true
    permalink: /infrastructure/:name/
  applications:
    source: "04-applications/"
    output: true
    permalink: /apps/:name/
  deployment:
    source: "05-deployment/"
    output: true
    permalink: /deploy/:name/
```

**Navigation Generation**:
```javascript
// Automatic navigation from markdown structure
const navStructure = {
  "Core System": {
    icon: "🎯",
    path: "/core/",
    children: [
      { title: "CLAUDE.md", path: "/core/claude/" },
      { title: "User Guide", path: "/core/user-guide/" },
      { title: "Utilities", path: "/core/utilities/" }
    ]
  },
  "Platform Vision": {
    icon: "🚀",
    path: "/platform/",
    children: [
      { title: "Interactive Platform", path: "/platform/interactive/" },
      { title: "Distributed Network", path: "/platform/distributed/" }
    ]
  }
};
```

### Live Status Integration

**Real-time Documentation Updates**:
- **Model Registry**: Live model performance metrics embedded in docs
- **Network Status**: Current IPFS/blockchain node statistics
- **Research Progress**: Automatically updated from GitHub Issues/Projects
- **Community Stats**: Contributor statistics and recent activity

**Dynamic Content Injection**:
```markdown
<!-- Live status widgets in documentation -->
{% include live-stats.html type="model_accuracy" model="sharktrack_v1.0" %}
{% include network-map.html %}
{% include recent-contributions.html limit=5 %}
```

### Cross-Reference System

**Automated Link Management**:
- **Internal Links**: Automatic conversion of relative paths
- **Anchor Generation**: Table of contents and deep linking
- **Broken Link Detection**: CI/CD validation of all references
- **Version Compatibility**: Link updates across documentation versions

**Search Integration**:
```javascript
// Full-text search across all documentation
const searchIndex = {
  "core": searchCoreSystem(),
  "platform": searchPlatformDocs(),
  "api": searchAPIReference(),
  "research": searchResearchPapers()
};
```

### Content Syndication

**Multi-format Output**:
- **Website**: Interactive HTML with live features
- **PDF**: Printable documentation via LaTeX generation
- **API Docs**: OpenAPI specification integration
- **Mobile**: Progressive Web App for field reference

**Content Distribution**:
- **GitHub Pages**: Primary hosting with global CDN
- **Mirror Sites**: Regional documentation mirrors
- **Offline Access**: Service worker caching for remote locations
- **API Integration**: Documentation embedded in platform apps

### Community Integration

**Collaborative Documentation**:
- **Edit Links**: Direct GitHub editing from documentation pages
- **Issue Integration**: Report documentation problems directly
- **Translation**: Multi-language support via Jekyll plugins
- **Contribution Tracking**: Documentation contribution metrics

**Quality Assurance**:
```yaml
# Documentation CI pipeline
documentation_quality:
  - markdown_lint: validate syntax
  - link_checker: verify all references
  - spelling_check: automated proofreading
  - accessibility: WCAG compliance testing
  - performance: page load optimization
```

This interlinked documentation strategy transforms the current local markdown structure into a dynamic, searchable, and continuously updated knowledge base that serves both technical users and the broader marine research community.

---

This comprehensive GitHub Pages website design provides a complete foundation for the SharkTrack platform with real-time statistics, interactive features, and seamless integration with the broader ecosystem.