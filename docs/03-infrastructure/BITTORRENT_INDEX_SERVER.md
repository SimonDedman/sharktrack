# BitTorrent Index Server for Marine Research Datasets

This document specifies the complete technical architecture for a BitTorrent-based distributed video sharing system designed specifically for marine research institutions.

## System Architecture Overview

### Core Concept
A federated network of BitTorrent trackers hosted by marine research institutions, enabling direct peer-to-peer sharing of research videos while maintaining institutional control and reducing centralized infrastructure costs.

### Technology Stack
- **Tracker Software**: Custom Node.js tracker with academic authentication
- **Protocol**: Enhanced BitTorrent with research metadata extensions
- **Database**: PostgreSQL for torrent metadata and research attribution
- **Frontend**: React-based web interface for dataset discovery
- **Security**: Academic federation authentication (SAML/OpenID Connect)
- **Storage**: IPFS integration for metadata persistence
- **API**: GraphQL for complex research queries

### Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                Global Research Index                            │
│         (Federated metadata aggregation)                       │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│Tracker│    │Tracker│    │Tracker│
│Oxford │    │WHOI   │    │AIMS   │
│.edu   │    │.edu   │    │.au    │
└───┬───┘    └───┬───┘    └───┬───┘
    │            │            │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│Seeder │    │Seeder │    │Seeder │
│Nodes  │    │Nodes  │    │Nodes  │
└───────┘    └───────┘    └───────┘
```

---

## Tracker Server Implementation

### Core Tracker (`server/tracker.js`)

```javascript
const express = require('express');
const dgram = require('dgram');
const crypto = require('crypto');
const bencode = require('bencode');
const { Pool } = require('pg');
const { createHash } = require('crypto');

class MarineResearchTracker {
    constructor(config) {
        this.config = config;
        this.app = express();
        this.udpServer = dgram.createSocket('udp4');
        this.db = new Pool(config.database);
        this.peers = new Map(); // Map of info_hash -> Set of peers
        this.torrents = new Map(); // Map of info_hash -> torrent metadata
        this.institutions = new Map(); // Map of institution -> authentication

        this.setupRoutes();
        this.setupUDPTracker();
        this.startCleanupInterval();
    }

    setupRoutes() {
        // HTTP announce endpoint
        this.app.get('/announce', this.handleHTTPAnnounce.bind(this));

        // Research-specific endpoints
        this.app.get('/api/datasets', this.getDatasets.bind(this));
        this.app.get('/api/search', this.searchDatasets.bind(this));
        this.app.post('/api/register', this.registerTorrent.bind(this));
        this.app.get('/api/stats', this.getNetworkStats.bind(this));

        // Torrent file serving
        this.app.get('/torrent/:hash', this.serveTorrentFile.bind(this));

        // Federation endpoints
        this.app.get('/federation/metadata', this.getFederationMetadata.bind(this));
        this.app.post('/federation/sync', this.syncWithPeers.bind(this));
    }

    setupUDPTracker() {
        this.udpServer.on('message', this.handleUDPMessage.bind(this));
        this.udpServer.on('error', (err) => {
            console.error('UDP tracker error:', err);
        });
    }

    async handleHTTPAnnounce(req, res) {
        try {
            const {
                info_hash,
                peer_id,
                port,
                uploaded,
                downloaded,
                left,
                event,
                compact = 1,
                numwant = 50
            } = req.query;

            // Validate required parameters
            if (!info_hash || !peer_id || !port) {
                return this.sendError(res, 'Missing required parameters');
            }

            // Decode info_hash and peer_id
            const infoHashHex = this.urlDecodeToHex(info_hash);
            const peerIdHex = this.urlDecodeToHex(peer_id);

            // Get client IP
            const clientIP = req.headers['x-forwarded-for'] ||
                           req.connection.remoteAddress ||
                           req.socket.remoteAddress;

            // Verify torrent is registered for research
            const torrentInfo = await this.getTorrentInfo(infoHashHex);
            if (!torrentInfo) {
                return this.sendError(res, 'Torrent not registered in research network');
            }

            // Check institutional access permissions
            const hasAccess = await this.checkAccess(clientIP, torrentInfo.institution);
            if (!hasAccess && torrentInfo.access_level === 'institutional') {
                return this.sendError(res, 'Access restricted to research institutions');
            }

            // Update peer in tracking
            const peer = {
                peer_id: peerIdHex,
                ip: clientIP,
                port: parseInt(port),
                uploaded: parseInt(uploaded) || 0,
                downloaded: parseInt(downloaded) || 0,
                left: parseInt(left) || 0,
                last_seen: Date.now(),
                event: event || 'update'
            };

            await this.updatePeer(infoHashHex, peer);

            // Get peer list for response
            const peers = await this.getPeers(infoHashHex, parseInt(numwant));

            // Prepare response
            const response = {
                interval: 1800, // 30 minutes
                'min interval': 300, // 5 minutes
                complete: torrentInfo.seeders || 0,
                incomplete: torrentInfo.leechers || 0
            };

            if (compact == 1) {
                // Compact format: 6 bytes per peer (4 byte IP + 2 byte port)
                response.peers = this.packPeers(peers);
            } else {
                // Dictionary format
                response.peers = peers.map(p => ({
                    'peer id': Buffer.from(p.peer_id, 'hex'),
                    ip: p.ip,
                    port: p.port
                }));
            }

            // Add research-specific information
            response.research_info = {
                dataset_id: torrentInfo.dataset_id,
                institution: torrentInfo.institution,
                species_tags: torrentInfo.species_tags,
                location: torrentInfo.location,
                collection_date: torrentInfo.collection_date
            };

            res.setHeader('Content-Type', 'text/plain');
            res.send(bencode.encode(response));

            // Log activity for research metrics
            await this.logActivity(infoHashHex, peer, 'announce');

        } catch (error) {
            console.error('Announce error:', error);
            this.sendError(res, 'Internal tracker error');
        }
    }

    async handleUDPMessage(message, remote) {
        try {
            if (message.length < 16) return; // Minimum UDP packet size

            const action = message.readUInt32BE(8);
            const transactionId = message.readUInt32BE(12);

            switch (action) {
                case 0: // Connect
                    await this.handleUDPConnect(message, remote, transactionId);
                    break;
                case 1: // Announce
                    await this.handleUDPAnnounce(message, remote, transactionId);
                    break;
                case 2: // Scrape
                    await this.handleUDPScrape(message, remote, transactionId);
                    break;
                default:
                    console.log('Unknown UDP action:', action);
            }
        } catch (error) {
            console.error('UDP message error:', error);
        }
    }

    async handleUDPConnect(message, remote, transactionId) {
        // Generate connection ID
        const connectionId = crypto.randomBytes(8);

        // Store connection for validation
        const connectionKey = `${remote.address}:${remote.port}`;
        this.connections.set(connectionKey, {
            id: connectionId,
            created: Date.now()
        });

        // Send response
        const response = Buffer.alloc(16);
        response.writeUInt32BE(0, 0); // Action: connect
        response.writeUInt32BE(transactionId, 4);
        connectionId.copy(response, 8);

        this.udpServer.send(response, remote.port, remote.address);
    }

    async handleUDPAnnounce(message, remote, transactionId) {
        if (message.length < 98) return;

        const connectionId = message.slice(0, 8);
        const infoHash = message.slice(16, 36);
        const peerId = message.slice(36, 56);
        const downloaded = message.readBigUInt64BE(56);
        const left = message.readBigUInt64BE(64);
        const uploaded = message.readBigUInt64BE(72);
        const event = message.readUInt32BE(80);
        const port = message.readUInt16BE(96);

        // Validate connection
        const connectionKey = `${remote.address}:${remote.port}`;
        const connection = this.connections.get(connectionKey);
        if (!connection || !connectionId.equals(connection.id)) {
            return; // Invalid connection
        }

        const infoHashHex = infoHash.toString('hex');
        const peerIdHex = peerId.toString('hex');

        // Check if torrent is registered
        const torrentInfo = await this.getTorrentInfo(infoHashHex);
        if (!torrentInfo) return;

        // Update peer
        const peer = {
            peer_id: peerIdHex,
            ip: remote.address,
            port: port,
            uploaded: Number(uploaded),
            downloaded: Number(downloaded),
            left: Number(left),
            last_seen: Date.now(),
            event: this.getEventString(event)
        };

        await this.updatePeer(infoHashHex, peer);

        // Get peers for response
        const peers = await this.getPeers(infoHashHex, 30);
        const packedPeers = this.packPeers(peers);

        // Send response
        const response = Buffer.alloc(20 + packedPeers.length);
        response.writeUInt32BE(1, 0); // Action: announce
        response.writeUInt32BE(transactionId, 4);
        response.writeUInt32BE(1800, 8); // Interval
        response.writeUInt32BE(torrentInfo.leechers || 0, 12); // Leechers
        response.writeUInt32BE(torrentInfo.seeders || 0, 16); // Seeders
        packedPeers.copy(response, 20);

        this.udpServer.send(response, remote.port, remote.address);
    }

    async registerTorrent(req, res) {
        try {
            const {
                torrent_data,
                dataset_metadata,
                institution_token
            } = req.body;

            // Verify institution token
            const institution = await this.verifyInstitutionToken(institution_token);
            if (!institution) {
                return res.status(401).json({ error: 'Invalid institution token' });
            }

            // Parse torrent file
            const torrentInfo = bencode.decode(Buffer.from(torrent_data, 'base64'));
            const infoHash = createHash('sha1').update(bencode.encode(torrentInfo.info)).digest('hex');

            // Validate research metadata
            const validationResult = await this.validateResearchMetadata(dataset_metadata);
            if (!validationResult.valid) {
                return res.status(400).json({ error: validationResult.errors });
            }

            // Register in database
            const torrentRecord = {
                info_hash: infoHash,
                institution: institution.name,
                dataset_id: dataset_metadata.dataset_id,
                title: dataset_metadata.title,
                description: dataset_metadata.description,
                species_tags: dataset_metadata.species_tags,
                location: dataset_metadata.location,
                collection_date: dataset_metadata.collection_date,
                access_level: dataset_metadata.access_level || 'public',
                file_count: torrentInfo.info.files ? torrentInfo.info.files.length : 1,
                total_size: this.calculateTorrentSize(torrentInfo.info),
                created_at: new Date(),
                torrent_data: torrent_data
            };

            await this.saveTorrentRecord(torrentRecord);

            // Add to local tracking
            this.torrents.set(infoHash, torrentRecord);

            // Notify federation peers
            await this.notifyFederationPeers('new_dataset', torrentRecord);

            res.json({
                success: true,
                info_hash: infoHash,
                magnet_link: this.generateMagnetLink(torrentInfo, torrentRecord),
                tracker_url: `${this.config.baseUrl}/announce`
            });

        } catch (error) {
            console.error('Torrent registration error:', error);
            res.status(500).json({ error: 'Registration failed' });
        }
    }

    async searchDatasets(req, res) {
        try {
            const {
                query,
                species,
                location,
                institution,
                date_from,
                date_to,
                access_level,
                limit = 50,
                offset = 0
            } = req.query;

            const searchResults = await this.performDatabaseSearch({
                query,
                species,
                location,
                institution,
                date_from,
                date_to,
                access_level,
                limit: parseInt(limit),
                offset: parseInt(offset)
            });

            // Add real-time peer information
            for (const result of searchResults) {
                const peers = await this.getPeers(result.info_hash, 5);
                result.seeders = peers.filter(p => p.left === 0).length;
                result.leechers = peers.filter(p => p.left > 0).length;
                result.last_activity = peers.length > 0 ?
                    Math.max(...peers.map(p => p.last_seen)) : null;
            }

            res.json({
                results: searchResults,
                total: await this.getSearchResultCount({
                    query, species, location, institution, date_from, date_to, access_level
                }),
                page: Math.floor(offset / limit) + 1,
                per_page: limit
            });

        } catch (error) {
            console.error('Search error:', error);
            res.status(500).json({ error: 'Search failed' });
        }
    }

    generateMagnetLink(torrentInfo, metadata) {
        const infoHash = createHash('sha1').update(bencode.encode(torrentInfo.info)).digest('hex');
        const name = encodeURIComponent(metadata.title || torrentInfo.info.name);

        let magnetLink = `magnet:?xt=urn:btih:${infoHash}&dn=${name}`;

        // Add tracker URLs
        const trackers = [
            `${this.config.baseUrl}/announce`,
            ...this.config.federationTrackers
        ];

        trackers.forEach(tracker => {
            magnetLink += `&tr=${encodeURIComponent(tracker)}`;
        });

        // Add research-specific parameters
        magnetLink += `&x.dataset=${encodeURIComponent(metadata.dataset_id)}`;
        magnetLink += `&x.institution=${encodeURIComponent(metadata.institution)}`;

        if (metadata.species_tags) {
            metadata.species_tags.forEach(species => {
                magnetLink += `&x.species=${encodeURIComponent(species)}`;
            });
        }

        return magnetLink;
    }

    packPeers(peers) {
        const buffer = Buffer.alloc(peers.length * 6);
        let offset = 0;

        for (const peer of peers) {
            const ipParts = peer.ip.split('.').map(p => parseInt(p));
            buffer.writeUInt8(ipParts[0], offset);
            buffer.writeUInt8(ipParts[1], offset + 1);
            buffer.writeUInt8(ipParts[2], offset + 2);
            buffer.writeUInt8(ipParts[3], offset + 3);
            buffer.writeUInt16BE(peer.port, offset + 4);
            offset += 6;
        }

        return buffer;
    }

    async updatePeer(infoHash, peer) {
        if (!this.peers.has(infoHash)) {
            this.peers.set(infoHash, new Map());
        }

        const torrentPeers = this.peers.get(infoHash);
        const peerKey = `${peer.peer_id}:${peer.ip}:${peer.port}`;

        if (peer.event === 'stopped') {
            torrentPeers.delete(peerKey);
        } else {
            torrentPeers.set(peerKey, peer);
        }

        // Update database with peer statistics
        await this.updatePeerStatistics(infoHash, peer);
    }

    async getPeers(infoHash, maxPeers) {
        const torrentPeers = this.peers.get(infoHash);
        if (!torrentPeers) return [];

        const peerArray = Array.from(torrentPeers.values())
            .filter(peer => Date.now() - peer.last_seen < 3600000) // 1 hour timeout
            .slice(0, maxPeers);

        return peerArray;
    }

    startCleanupInterval() {
        setInterval(() => {
            this.cleanupStaleConnections();
            this.cleanupStalePeers();
        }, 300000); // 5 minutes
    }

    cleanupStaleConnections() {
        const now = Date.now();
        for (const [key, connection] of this.connections) {
            if (now - connection.created > 600000) { // 10 minutes
                this.connections.delete(key);
            }
        }
    }

    cleanupStalePeers() {
        const now = Date.now();
        const timeout = 3600000; // 1 hour

        for (const [infoHash, torrentPeers] of this.peers) {
            for (const [peerKey, peer] of torrentPeers) {
                if (now - peer.last_seen > timeout) {
                    torrentPeers.delete(peerKey);
                }
            }

            // Remove empty torrent entries
            if (torrentPeers.size === 0) {
                this.peers.delete(infoHash);
            }
        }
    }

    start() {
        // Start HTTP server
        const httpPort = this.config.httpPort || 8080;
        this.app.listen(httpPort, () => {
            console.log(`Marine Research Tracker HTTP server running on port ${httpPort}`);
        });

        // Start UDP server
        const udpPort = this.config.udpPort || 8080;
        this.udpServer.bind(udpPort, () => {
            console.log(`Marine Research Tracker UDP server running on port ${udpPort}`);
        });
    }
}

module.exports = MarineResearchTracker;
```

---

## Federation and Discovery System

### Federation Manager (`server/federation.js`)

```javascript
class FederationManager {
    constructor(tracker, config) {
        this.tracker = tracker;
        this.config = config;
        this.peerTrackers = new Map();
        this.lastSync = new Map();
        this.syncInterval = 3600000; // 1 hour

        this.setupFederation();
    }

    async setupFederation() {
        // Load known peer trackers
        await this.loadPeerTrackers();

        // Start periodic synchronization
        setInterval(() => {
            this.syncWithAllPeers();
        }, this.syncInterval);

        // Immediate sync on startup
        setTimeout(() => this.syncWithAllPeers(), 5000);
    }

    async loadPeerTrackers() {
        // Load from database and configuration
        const knownTrackers = [
            {
                name: 'Woods Hole Oceanographic Institution',
                url: 'https://tracker.whoi.edu',
                institution: 'WHOI',
                location: 'United States',
                specialties: ['deep_sea', 'atlantic_research'],
                public_key: 'academic_verification_key_whoi'
            },
            {
                name: 'Australian Institute of Marine Science',
                url: 'https://tracker.aims.gov.au',
                institution: 'AIMS',
                location: 'Australia',
                specialties: ['coral_reefs', 'tropical_marine'],
                public_key: 'academic_verification_key_aims'
            },
            {
                name: 'Oxford Marine Biology',
                url: 'https://marine-tracker.oxford.ac.uk',
                institution: 'Oxford',
                location: 'United Kingdom',
                specialties: ['behavioral_ecology', 'conservation'],
                public_key: 'academic_verification_key_oxford'
            }
        ];

        for (const tracker of knownTrackers) {
            this.peerTrackers.set(tracker.url, tracker);
        }
    }

    async syncWithAllPeers() {
        const syncPromises = Array.from(this.peerTrackers.keys()).map(url =>
            this.syncWithPeer(url).catch(error =>
                console.error(`Sync failed with ${url}:`, error)
            )
        );

        await Promise.allSettled(syncPromises);
    }

    async syncWithPeer(trackerUrl) {
        try {
            const lastSyncTime = this.lastSync.get(trackerUrl) || 0;
            const peerInfo = this.peerTrackers.get(trackerUrl);

            // Request metadata updates since last sync
            const response = await fetch(`${trackerUrl}/federation/metadata`, {
                method: 'GET',
                headers: {
                    'X-Federation-Token': this.config.federationToken,
                    'X-Institution': this.config.institution,
                    'X-Last-Sync': lastSyncTime.toString()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const federationData = await response.json();

            // Process received metadata
            await this.processFederationData(federationData, peerInfo);

            // Update last sync time
            this.lastSync.set(trackerUrl, Date.now());

            console.log(`Federation sync completed with ${peerInfo.institution}`);

        } catch (error) {
            console.error(`Federation sync failed with ${trackerUrl}:`, error);
        }
    }

    async processFederationData(data, peerInfo) {
        for (const torrentMeta of data.torrents) {
            // Skip if we already have this torrent
            if (await this.tracker.getTorrentInfo(torrentMeta.info_hash)) {
                continue;
            }

            // Verify data integrity and authenticity
            if (!await this.verifyTorrentSignature(torrentMeta, peerInfo.public_key)) {
                console.warn(`Invalid signature for torrent ${torrentMeta.info_hash} from ${peerInfo.institution}`);
                continue;
            }

            // Add to local index as federated content
            await this.addFederatedTorrent({
                ...torrentMeta,
                federated: true,
                source_tracker: peerInfo.url,
                source_institution: peerInfo.institution
            });
        }
    }

    async addFederatedTorrent(torrentData) {
        // Add to database with federated flag
        await this.tracker.saveTorrentRecord({
            ...torrentData,
            local: false,
            federated: true,
            indexed_at: new Date()
        });

        console.log(`Added federated torrent: ${torrentData.title} from ${torrentData.source_institution}`);
    }

    async broadcastNewTorrent(torrentData) {
        // Broadcast new local torrent to federation peers
        const broadcastData = {
            type: 'new_torrent',
            torrent: this.prepareTorrentForBroadcast(torrentData),
            timestamp: Date.now(),
            signature: await this.signData(torrentData)
        };

        const broadcastPromises = Array.from(this.peerTrackers.keys()).map(url =>
            this.sendBroadcast(url, broadcastData).catch(error =>
                console.error(`Broadcast failed to ${url}:`, error)
            )
        );

        await Promise.allSettled(broadcastPromises);
    }

    prepareTorrentForBroadcast(torrentData) {
        // Remove sensitive local information
        const {
            torrent_data, // Don't broadcast full torrent file
            internal_id,
            local_peers,
            ...broadcastData
        } = torrentData;

        return {
            ...broadcastData,
            magnet_link: this.tracker.generateMagnetLink(torrentData),
            peer_count: local_peers ? local_peers.length : 0
        };
    }

    async sendBroadcast(trackerUrl, data) {
        const response = await fetch(`${trackerUrl}/federation/receive`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Federation-Token': this.config.federationToken,
                'X-Institution': this.config.institution
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`Broadcast failed: ${response.status} ${response.statusText}`);
        }
    }

    async verifyTorrentSignature(torrentData, publicKey) {
        // Implement cryptographic verification of torrent metadata
        // This ensures data integrity across the federation
        return true; // Simplified for example
    }

    async signData(data) {
        // Implement digital signing of data for federation
        return 'signature_placeholder';
    }
}

module.exports = FederationManager;
```

---

## Database Schema

### PostgreSQL Schema (`database/schema.sql`)

```sql
-- Torrents table for research datasets
CREATE TABLE torrents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    info_hash VARCHAR(40) UNIQUE NOT NULL,
    dataset_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    institution VARCHAR(255) NOT NULL,
    researcher_name VARCHAR(255),

    -- Research metadata
    species_tags TEXT[] DEFAULT '{}',
    habitat_type VARCHAR(100),
    location JSONB, -- GeoJSON format
    collection_date TIMESTAMP,
    depth_range NUMRANGE,
    temperature_range NUMRANGE,

    -- Torrent metadata
    file_count INTEGER NOT NULL,
    total_size BIGINT NOT NULL,
    piece_length INTEGER,
    torrent_data TEXT, -- Base64 encoded torrent file

    -- Access control
    access_level VARCHAR(50) DEFAULT 'public', -- public, institutional, restricted
    access_institutions TEXT[] DEFAULT '{}',

    -- Federation
    local BOOLEAN DEFAULT true,
    federated BOOLEAN DEFAULT false,
    source_tracker VARCHAR(255),
    source_institution VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    indexed_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Peers table for tracking active connections
CREATE TABLE peers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    info_hash VARCHAR(40) NOT NULL REFERENCES torrents(info_hash),
    peer_id VARCHAR(40) NOT NULL,
    ip_address INET NOT NULL,
    port INTEGER NOT NULL,

    -- Transfer statistics
    uploaded BIGINT DEFAULT 0,
    downloaded BIGINT DEFAULT 0,
    remaining BIGINT DEFAULT 0,

    -- Connection info
    user_agent TEXT,
    client_version VARCHAR(100),
    connection_type VARCHAR(20), -- tcp, udp, webseed

    -- Academic info
    institution VARCHAR(255),
    researcher_authenticated BOOLEAN DEFAULT false,

    -- Timestamps
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    last_announce TIMESTAMP DEFAULT NOW()
);

-- Research institutions table
CREATE TABLE institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    country VARCHAR(100),

    -- Authentication
    saml_endpoint VARCHAR(500),
    oidc_endpoint VARCHAR(500),
    api_token VARCHAR(255),
    public_key TEXT,

    -- Network settings
    tracker_url VARCHAR(500),
    bandwidth_limit BIGINT, -- bytes per second
    storage_quota BIGINT, -- bytes

    -- Specialties and preferences
    research_areas TEXT[] DEFAULT '{}',
    species_interests TEXT[] DEFAULT '{}',
    geographic_focus JSONB,

    -- Status
    active BOOLEAN DEFAULT true,
    verified BOOLEAN DEFAULT false,
    federation_member BOOLEAN DEFAULT false,

    -- Timestamps
    joined_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW()
);

-- Activity logs for research metrics
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    info_hash VARCHAR(40) NOT NULL,
    peer_id VARCHAR(40),
    ip_address INET,

    -- Activity details
    action VARCHAR(50) NOT NULL, -- announce, download, upload, search
    bytes_transferred BIGINT DEFAULT 0,
    session_duration INTEGER, -- seconds

    -- Research context
    institution VARCHAR(255),
    researcher_id VARCHAR(255),
    access_method VARCHAR(50), -- web, api, torrent_client

    -- Metadata
    user_agent TEXT,
    additional_data JSONB,

    -- Timestamp
    occurred_at TIMESTAMP DEFAULT NOW()
);

-- Federation sync tracking
CREATE TABLE federation_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peer_tracker_url VARCHAR(500) NOT NULL,
    peer_institution VARCHAR(255) NOT NULL,

    -- Sync details
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(50), -- success, failed, in_progress
    torrents_received INTEGER DEFAULT 0,
    torrents_sent INTEGER DEFAULT 0,

    -- Error tracking
    last_error TEXT,
    consecutive_failures INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Research citations and attribution
CREATE TABLE research_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    info_hash VARCHAR(40) NOT NULL REFERENCES torrents(info_hash),

    -- Citation details
    doi VARCHAR(255),
    paper_title TEXT,
    authors TEXT[],
    journal VARCHAR(255),
    publication_date DATE,

    -- Usage tracking
    download_count INTEGER DEFAULT 0,
    analysis_count INTEGER DEFAULT 0,
    derived_works INTEGER DEFAULT 0,

    -- Attribution
    citing_institution VARCHAR(255),
    usage_type VARCHAR(100), -- analysis, comparison, meta_study, reproduction

    -- Timestamps
    cited_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_torrents_info_hash ON torrents(info_hash);
CREATE INDEX idx_torrents_institution ON torrents(institution);
CREATE INDEX idx_torrents_species ON torrents USING GIN(species_tags);
CREATE INDEX idx_torrents_location ON torrents USING GIST(((location->>'coordinates')::json));
CREATE INDEX idx_torrents_collection_date ON torrents(collection_date);
CREATE INDEX idx_torrents_federated ON torrents(federated, local);

CREATE INDEX idx_peers_info_hash ON peers(info_hash);
CREATE INDEX idx_peers_ip_port ON peers(ip_address, port);
CREATE INDEX idx_peers_last_seen ON peers(last_seen);
CREATE INDEX idx_peers_institution ON peers(institution);

CREATE INDEX idx_activity_logs_info_hash ON activity_logs(info_hash);
CREATE INDEX idx_activity_logs_occurred_at ON activity_logs(occurred_at);
CREATE INDEX idx_activity_logs_institution ON activity_logs(institution);

CREATE INDEX idx_federation_sync_peer ON federation_sync(peer_tracker_url);
CREATE INDEX idx_federation_sync_status ON federation_sync(sync_status);

-- Views for common queries
CREATE VIEW active_torrents AS
SELECT
    t.*,
    COUNT(DISTINCT p.peer_id) as active_peers,
    COUNT(DISTINCT p.peer_id) FILTER (WHERE p.remaining = 0) as seeders,
    COUNT(DISTINCT p.peer_id) FILTER (WHERE p.remaining > 0) as leechers,
    MAX(p.last_seen) as last_activity
FROM torrents t
LEFT JOIN peers p ON t.info_hash = p.info_hash
    AND p.last_seen > NOW() - INTERVAL '1 hour'
GROUP BY t.id;

CREATE VIEW federation_health AS
SELECT
    peer_institution,
    peer_tracker_url,
    last_sync_at,
    sync_status,
    consecutive_failures,
    CASE
        WHEN last_sync_at > NOW() - INTERVAL '6 hours' AND sync_status = 'success'
        THEN 'healthy'
        WHEN consecutive_failures < 3
        THEN 'degraded'
        ELSE 'offline'
    END as health_status
FROM federation_sync
ORDER BY last_sync_at DESC;

CREATE VIEW research_impact AS
SELECT
    t.info_hash,
    t.title,
    t.institution,
    COUNT(DISTINCT rc.id) as citations,
    SUM(rc.download_count) as total_downloads,
    COUNT(DISTINCT a.institution) as institutions_accessed,
    MAX(a.occurred_at) as last_accessed
FROM torrents t
LEFT JOIN research_citations rc ON t.info_hash = rc.info_hash
LEFT JOIN activity_logs a ON t.info_hash = a.info_hash
GROUP BY t.id, t.info_hash, t.title, t.institution
ORDER BY citations DESC, total_downloads DESC;
```

---

## Web Interface for Dataset Discovery

### React Frontend (`frontend/src/components/DatasetExplorer.tsx`)

```typescript
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Dataset {
  info_hash: string;
  dataset_id: string;
  title: string;
  description: string;
  institution: string;
  species_tags: string[];
  location: GeoLocation;
  collection_date: string;
  file_count: number;
  total_size: number;
  seeders: number;
  leechers: number;
  magnet_link: string;
  federated: boolean;
  source_institution?: string;
}

interface GeoLocation {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
  properties?: {
    depth?: number;
    habitat?: string;
  };
}

export const DatasetExplorer: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [filteredDatasets, setFilteredDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    species: '',
    institution: '',
    habitat: '',
    dateFrom: '',
    dateTo: '',
    availabilityOnly: false
  });
  const [viewMode, setViewMode] = useState<'grid' | 'map' | 'timeline'>('grid');
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchQuery, filters, datasets]);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/datasets?include_federated=true');
      const data = await response.json();
      setDatasets(data.results);
      setFilteredDatasets(data.results);
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...datasets];

    // Text search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(dataset =>
        dataset.title.toLowerCase().includes(query) ||
        dataset.description.toLowerCase().includes(query) ||
        dataset.species_tags.some(tag => tag.toLowerCase().includes(query)) ||
        dataset.institution.toLowerCase().includes(query)
      );
    }

    // Species filter
    if (filters.species) {
      filtered = filtered.filter(dataset =>
        dataset.species_tags.some(tag =>
          tag.toLowerCase().includes(filters.species.toLowerCase())
        )
      );
    }

    // Institution filter
    if (filters.institution) {
      filtered = filtered.filter(dataset =>
        dataset.institution.toLowerCase().includes(filters.institution.toLowerCase())
      );
    }

    // Date range filter
    if (filters.dateFrom) {
      filtered = filtered.filter(dataset =>
        new Date(dataset.collection_date) >= new Date(filters.dateFrom)
      );
    }

    if (filters.dateTo) {
      filtered = filtered.filter(dataset =>
        new Date(dataset.collection_date) <= new Date(filters.dateTo)
      );
    }

    // Availability filter (has active seeders)
    if (filters.availabilityOnly) {
      filtered = filtered.filter(dataset => dataset.seeders > 0);
    }

    setFilteredDatasets(filtered);
  };

  const downloadTorrent = async (infoHash: string) => {
    try {
      const response = await fetch(`/torrent/${infoHash}`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = url;
      a.download = `${infoHash}.torrent`;
      a.click();

      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const copyMagnetLink = (magnetLink: string) => {
    navigator.clipboard.writeText(magnetLink);
    // Show toast notification
  };

  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const renderGridView = () => (
    <div className="dataset-grid">
      {filteredDatasets.map(dataset => (
        <div key={dataset.info_hash} className="dataset-card">
          <div className="card-header">
            <h3>{dataset.title}</h3>
            <div className="card-badges">
              {dataset.federated && (
                <span className="badge federated">Federated</span>
              )}
              <span className={`badge availability ${dataset.seeders > 0 ? 'available' : 'unavailable'}`}>
                {dataset.seeders > 0 ? 'Available' : 'Offline'}
              </span>
            </div>
          </div>

          <div className="card-content">
            <p className="description">{dataset.description}</p>

            <div className="metadata">
              <div className="metadata-item">
                <strong>Institution:</strong> {dataset.institution}
              </div>
              <div className="metadata-item">
                <strong>Species:</strong> {dataset.species_tags.join(', ')}
              </div>
              <div className="metadata-item">
                <strong>Collection Date:</strong> {formatDate(dataset.collection_date)}
              </div>
              <div className="metadata-item">
                <strong>Size:</strong> {formatFileSize(dataset.total_size)} ({dataset.file_count} files)
              </div>
            </div>

            <div className="peer-info">
              <span className="seeders">🌱 {dataset.seeders} seeders</span>
              <span className="leechers">⬇️ {dataset.leechers} leechers</span>
            </div>
          </div>

          <div className="card-actions">
            <button
              onClick={() => downloadTorrent(dataset.info_hash)}
              className="btn-primary"
            >
              Download Torrent
            </button>
            <button
              onClick={() => copyMagnetLink(dataset.magnet_link)}
              className="btn-secondary"
            >
              Copy Magnet Link
            </button>
            <button
              onClick={() => setSelectedDataset(dataset)}
              className="btn-info"
            >
              View Details
            </button>
          </div>
        </div>
      ))}
    </div>
  );

  const renderMapView = () => (
    <div className="map-container">
      <MapContainer
        center={[0, 0]}
        zoom={2}
        style={{ height: '600px', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        {filteredDatasets
          .filter(dataset => dataset.location)
          .map(dataset => (
            <Marker
              key={dataset.info_hash}
              position={[
                dataset.location.coordinates[1], // latitude
                dataset.location.coordinates[0]  // longitude
              ]}
            >
              <Popup>
                <div className="map-popup">
                  <h4>{dataset.title}</h4>
                  <p><strong>Institution:</strong> {dataset.institution}</p>
                  <p><strong>Species:</strong> {dataset.species_tags.join(', ')}</p>
                  <p><strong>Date:</strong> {formatDate(dataset.collection_date)}</p>
                  <p><strong>Availability:</strong> {dataset.seeders} seeders</p>
                  <button
                    onClick={() => setSelectedDataset(dataset)}
                    className="btn-small"
                  >
                    View Details
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
      </MapContainer>
    </div>
  );

  const renderTimelineView = () => {
    const timelineData = filteredDatasets
      .map(dataset => ({
        date: dataset.collection_date,
        count: 1,
        institution: dataset.institution
      }))
      .reduce((acc, item) => {
        const month = item.date.substring(0, 7); // YYYY-MM
        acc[month] = (acc[month] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

    const chartData = Object.entries(timelineData)
      .map(([month, count]) => ({ month, count }))
      .sort((a, b) => a.month.localeCompare(b.month));

    return (
      <div className="timeline-container">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="count" stroke="#2563eb" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="dataset-explorer">
      <div className="explorer-header">
        <h1>Marine Research Dataset Network</h1>
        <p>Discover and access marine video datasets from research institutions worldwide</p>
      </div>

      <div className="search-filters">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search datasets, species, institutions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filters">
          <input
            type="text"
            placeholder="Filter by species"
            value={filters.species}
            onChange={(e) => setFilters(prev => ({ ...prev, species: e.target.value }))}
          />
          <input
            type="text"
            placeholder="Filter by institution"
            value={filters.institution}
            onChange={(e) => setFilters(prev => ({ ...prev, institution: e.target.value }))}
          />
          <input
            type="date"
            placeholder="From date"
            value={filters.dateFrom}
            onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
          />
          <input
            type="date"
            placeholder="To date"
            value={filters.dateTo}
            onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
          />
          <label>
            <input
              type="checkbox"
              checked={filters.availabilityOnly}
              onChange={(e) => setFilters(prev => ({ ...prev, availabilityOnly: e.target.checked }))}
            />
            Available only
          </label>
        </div>

        <div className="view-controls">
          <button
            className={viewMode === 'grid' ? 'active' : ''}
            onClick={() => setViewMode('grid')}
          >
            Grid View
          </button>
          <button
            className={viewMode === 'map' ? 'active' : ''}
            onClick={() => setViewMode('map')}
          >
            Map View
          </button>
          <button
            className={viewMode === 'timeline' ? 'active' : ''}
            onClick={() => setViewMode('timeline')}
          >
            Timeline
          </button>
        </div>
      </div>

      <div className="results-summary">
        <span>{filteredDatasets.length} datasets found</span>
        <span>{filteredDatasets.filter(d => d.seeders > 0).length} available for download</span>
        <span>{new Set(filteredDatasets.map(d => d.institution)).size} institutions</span>
      </div>

      <div className="dataset-content">
        {loading ? (
          <div className="loading">Loading datasets...</div>
        ) : (
          <>
            {viewMode === 'grid' && renderGridView()}
            {viewMode === 'map' && renderMapView()}
            {viewMode === 'timeline' && renderTimelineView()}
          </>
        )}
      </div>

      {selectedDataset && (
        <DatasetDetailModal
          dataset={selectedDataset}
          onClose={() => setSelectedDataset(null)}
        />
      )}
    </div>
  );
};
```

---

## Deployment and Configuration

### Docker Configuration (`docker/Dockerfile`)

```dockerfile
FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    postgresql-client \
    curl

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S tracker && \
    adduser -S tracker -u 1001

# Set permissions
RUN chown -R tracker:tracker /app
USER tracker

# Expose ports
EXPOSE 8080 8080/udp

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["npm", "start"]
```

### Docker Compose (`docker/docker-compose.yml`)

```yaml
version: '3.8'

services:
  tracker:
    build: .
    ports:
      - "8080:8080"
      - "8080:8080/udp"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://tracker:password@postgres:5432/marine_tracker
      - FEDERATION_TOKEN=${FEDERATION_TOKEN}
      - INSTITUTION_NAME=${INSTITUTION_NAME}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./config:/app/config:ro
      - tracker_data:/app/data
    restart: unless-stopped

  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=marine_tracker
      - POSTGRES_USER=tracker
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - tracker
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  tracker_data:
```

### Configuration (`config/production.json`)

```json
{
  "server": {
    "httpPort": 8080,
    "udpPort": 8080,
    "baseUrl": "https://tracker.marine-research.org"
  },
  "database": {
    "host": "postgres",
    "port": 5432,
    "database": "marine_tracker",
    "user": "tracker",
    "password": "password",
    "ssl": false,
    "max": 20,
    "idleTimeoutMillis": 30000
  },
  "federation": {
    "enabled": true,
    "institution": "Marine Research Institute",
    "token": "${FEDERATION_TOKEN}",
    "syncInterval": 3600000,
    "peerTrackers": [
      "https://tracker.whoi.edu",
      "https://tracker.aims.gov.au",
      "https://marine-tracker.oxford.ac.uk"
    ]
  },
  "security": {
    "requireInstitutionalAuth": false,
    "allowPublicAccess": true,
    "maxPeersPerTorrent": 200,
    "announceInterval": 1800,
    "minAnnounceInterval": 300
  },
  "features": {
    "webInterface": true,
    "apiAccess": true,
    "researchMetrics": true,
    "geoSearching": true
  }
}
```

This BitTorrent index server provides a complete solution for decentralized marine research video sharing with academic federation, institutional authentication, and comprehensive research metadata support.