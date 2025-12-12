# Webcam Upload Portal - Technical Specification

This document specifies the complete technical implementation for direct webcam data upload with GPS metadata integration and real-time processing capabilities.

## Portal Architecture

### Technology Stack
- **Frontend**: React.js with TypeScript for type safety
- **Camera Integration**: WebRTC MediaDevices API with getUserMedia()
- **GPS/Location**: Geolocation API with fallback to IP-based location
- **Upload Backend**: Node.js with Express and Multer for file handling
- **Real-time Updates**: Socket.IO for upload progress and processing status
- **Video Processing**: FFmpeg integration for format conversion and metadata embedding
- **Storage**: AWS S3 or local storage with metadata database integration
- **Authentication**: JWT-based authentication with optional researcher accounts

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Webcam Upload Portal                         │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React)          │  Backend (Node.js)                 │
│  ├── Camera Interface      │  ├── Upload Handler                │
│  ├── GPS Integration       │  ├── Metadata Processor            │
│  ├── Upload Progress       │  ├── Video Converter               │
│  └── Preview & Controls    │  └── Database Integration          │
├─────────────────────────────────────────────────────────────────┤
│                    Processing Pipeline                          │
│  Video → Metadata → Storage → Queue → SharkTrack → Results     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend Implementation

### Main Upload Component (`components/WebcamUpload.tsx`)

```typescript
import React, { useState, useRef, useEffect } from 'react';
import { useCamera } from '../hooks/useCamera';
import { useGPS } from '../hooks/useGPS';
import { useUpload } from '../hooks/useUpload';
import { VideoPreview } from './VideoPreview';
import { UploadProgress } from './UploadProgress';
import { MetadataForm } from './MetadataForm';

interface WebcamUploadProps {
  onUploadComplete?: (result: UploadResult) => void;
  maxDuration?: number; // seconds
  maxFileSize?: number; // bytes
}

interface UploadResult {
  videoId: string;
  filename: string;
  duration: number;
  location: GPSCoordinates;
  processingStatus: 'queued' | 'processing' | 'completed';
}

interface GPSCoordinates {
  latitude: number;
  longitude: number;
  accuracy: number;
  timestamp: number;
  source: 'gps' | 'network' | 'manual';
}

export const WebcamUpload: React.FC<WebcamUploadProps> = ({
  onUploadComplete,
  maxDuration = 1800, // 30 minutes default
  maxFileSize = 2 * 1024 * 1024 * 1024 // 2GB default
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [recordedVideo, setRecordedVideo] = useState<Blob | null>(null);
  const [showMetadataForm, setShowMetadataForm] = useState(false);

  // Custom hooks for camera, GPS, and upload functionality
  const {
    stream,
    isSupported: cameraSupported,
    permissions,
    initializeCamera,
    stopCamera
  } = useCamera();

  const {
    coordinates,
    isSupported: gpsSupported,
    accuracy,
    requestLocation
  } = useGPS();

  const {
    uploadFile,
    uploadProgress,
    isUploading,
    uploadError
  } = useUpload();

  // Initialize camera on component mount
  useEffect(() => {
    initializeCamera({
      video: {
        width: { ideal: 1920 },
        height: { ideal: 1080 },
        frameRate: { ideal: 30 }
      },
      audio: true
    });

    return () => {
      stopCamera();
    };
  }, []);

  // Setup video stream
  useEffect(() => {
    if (stream && videoRef.current) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  // Recording duration timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingDuration(prev => {
          if (prev >= maxDuration) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording, maxDuration]);

  const startRecording = async () => {
    if (!stream) return;

    try {
      // Request GPS location before recording
      await requestLocation();

      // Setup MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm;codecs=vp9,opus'
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        setRecordedVideo(blob);
        setShowMetadataForm(true);
      };

      mediaRecorder.start(1000); // Capture data every second
      setIsRecording(true);
      setRecordingDuration(0);

    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleMetadataSubmit = async (metadata: VideoMetadata) => {
    if (!recordedVideo || !coordinates) return;

    const uploadData = {
      videoFile: recordedVideo,
      metadata: {
        ...metadata,
        duration: recordingDuration,
        location: coordinates,
        recordingDate: new Date().toISOString(),
        deviceInfo: {
          userAgent: navigator.userAgent,
          platform: navigator.platform,
          language: navigator.language
        }
      }
    };

    try {
      const result = await uploadFile(uploadData);
      if (onUploadComplete) {
        onUploadComplete(result);
      }
      // Reset for next recording
      setRecordedVideo(null);
      setShowMetadataForm(false);
      setRecordingDuration(0);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins:02d}:${secs:02d}`;
  };

  if (!cameraSupported) {
    return (
      <div className="upload-error">
        <h3>Camera Not Supported</h3>
        <p>Your browser doesn't support camera access. Please use a modern browser.</p>
      </div>
    );
  }

  if (permissions === 'denied') {
    return (
      <div className="upload-error">
        <h3>Camera Permission Denied</h3>
        <p>Please enable camera access to record videos.</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="webcam-upload">
      {showMetadataForm ? (
        <MetadataForm
          videoBlob={recordedVideo}
          duration={recordingDuration}
          location={coordinates}
          onSubmit={handleMetadataSubmit}
          onCancel={() => setShowMetadataForm(false)}
        />
      ) : (
        <>
          <div className="camera-interface">
            <div className="video-container">
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="camera-preview"
              />

              {isRecording && (
                <div className="recording-overlay">
                  <div className="recording-indicator">
                    <span className="recording-dot"></span>
                    REC {formatDuration(recordingDuration)}
                  </div>
                  <div className="duration-warning">
                    {recordingDuration > maxDuration * 0.9 && (
                      <span>Approaching maximum duration</span>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="camera-controls">
              <button
                className={`record-button ${isRecording ? 'recording' : ''}`}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={!stream || permissions === 'pending'}
              >
                {isRecording ? 'Stop Recording' : 'Start Recording'}
              </button>

              <div className="recording-info">
                <span>Duration: {formatDuration(recordingDuration)} / {formatDuration(maxDuration)}</span>
              </div>
            </div>
          </div>

          <div className="status-panel">
            <div className="gps-status">
              <h4>Location Status</h4>
              {coordinates ? (
                <div className="gps-info">
                  <span>✅ Location acquired</span>
                  <div className="coordinates">
                    Lat: {coordinates.latitude.toFixed(6)}<br/>
                    Lng: {coordinates.longitude.toFixed(6)}<br/>
                    Accuracy: ±{accuracy}m
                  </div>
                </div>
              ) : (
                <div className="gps-warning">
                  <span>⚠️ Location not available</span>
                  <p>Videos will be uploaded without GPS data</p>
                </div>
              )}
            </div>

            <div className="camera-status">
              <h4>Camera Status</h4>
              <span>{stream ? '✅ Camera active' : '⏳ Initializing camera...'}</span>
            </div>
          </div>
        </>
      )}

      {isUploading && (
        <UploadProgress
          progress={uploadProgress}
          filename="recorded-video.webm"
          error={uploadError}
        />
      )}
    </div>
  );
};
```

### Custom Hooks

#### Camera Hook (`hooks/useCamera.ts`)

```typescript
import { useState, useEffect, useCallback } from 'react';

interface CameraPermissions {
  camera: 'granted' | 'denied' | 'pending';
  microphone: 'granted' | 'denied' | 'pending';
}

interface CameraConstraints {
  video: MediaTrackConstraints | boolean;
  audio: MediaTrackConstraints | boolean;
}

export const useCamera = () => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  const [permissions, setPermissions] = useState<'granted' | 'denied' | 'pending'>('pending');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check browser support
    setIsSupported(!!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia));
  }, []);

  const initializeCamera = useCallback(async (constraints: CameraConstraints) => {
    if (!isSupported) return;

    try {
      setPermissions('pending');
      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);
      setPermissions('granted');
      setError(null);
    } catch (err: any) {
      console.error('Camera initialization failed:', err);

      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setPermissions('denied');
        setError('Camera permission denied');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('No camera device found');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setError('Camera is already in use by another application');
      } else {
        setError('Failed to access camera');
      }
    }
  }, [isSupported]);

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  }, [stream]);

  const switchCamera = useCallback(async (deviceId?: string) => {
    stopCamera();
    await initializeCamera({
      video: deviceId ? { deviceId: { exact: deviceId } } : true,
      audio: true
    });
  }, [stopCamera, initializeCamera]);

  return {
    stream,
    isSupported,
    permissions,
    error,
    initializeCamera,
    stopCamera,
    switchCamera
  };
};
```

#### GPS Hook (`hooks/useGPS.ts`)

```typescript
import { useState, useEffect, useCallback } from 'react';

interface GPSCoordinates {
  latitude: number;
  longitude: number;
  accuracy: number;
  timestamp: number;
  source: 'gps' | 'network' | 'manual';
}

export const useGPS = () => {
  const [coordinates, setCoordinates] = useState<GPSCoordinates | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  const [accuracy, setAccuracy] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsSupported('geolocation' in navigator);
  }, []);

  const requestLocation = useCallback(async (): Promise<GPSCoordinates | null> => {
    if (!isSupported) return null;

    return new Promise((resolve, reject) => {
      const options: PositionOptions = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      };

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords: GPSCoordinates = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp,
            source: position.coords.accuracy < 100 ? 'gps' : 'network'
          };
          setCoordinates(coords);
          setAccuracy(position.coords.accuracy);
          setError(null);
          resolve(coords);
        },
        (err) => {
          console.error('Geolocation error:', err);
          let errorMessage = 'Location access failed';

          switch (err.code) {
            case err.PERMISSION_DENIED:
              errorMessage = 'Location permission denied';
              break;
            case err.POSITION_UNAVAILABLE:
              errorMessage = 'Location unavailable';
              break;
            case err.TIMEOUT:
              errorMessage = 'Location request timeout';
              break;
          }

          setError(errorMessage);
          reject(new Error(errorMessage));
        },
        options
      );
    });
  }, [isSupported]);

  const watchPosition = useCallback(() => {
    if (!isSupported) return null;

    const options: PositionOptions = {
      enableHighAccuracy: true,
      maximumAge: 60000, // 1 minute
      timeout: 15000
    };

    return navigator.geolocation.watchPosition(
      (position) => {
        const coords: GPSCoordinates = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp,
          source: position.coords.accuracy < 100 ? 'gps' : 'network'
        };
        setCoordinates(coords);
        setAccuracy(position.coords.accuracy);
      },
      (err) => {
        console.error('Position watch error:', err);
        setError('Failed to track location');
      },
      options
    );
  }, [isSupported]);

  return {
    coordinates,
    isSupported,
    accuracy,
    error,
    requestLocation,
    watchPosition
  };
};
```

### Upload Hook (`hooks/useUpload.ts`)

```typescript
import { useState, useCallback } from 'react';
import io from 'socket.io-client';

interface UploadData {
  videoFile: Blob;
  metadata: VideoMetadata;
}

interface VideoMetadata {
  title: string;
  description: string;
  location: GPSCoordinates;
  habitat: string;
  depth?: number;
  temperature?: number;
  visibility?: number;
  researcherName: string;
  institution: string;
  duration: number;
  recordingDate: string;
  deviceInfo: any;
}

export const useUpload = () => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [socket, setSocket] = useState<any>(null);

  const uploadFile = useCallback(async (uploadData: UploadData) => {
    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('video', uploadData.videoFile, 'recording.webm');
      formData.append('metadata', JSON.stringify(uploadData.metadata));

      // Setup Socket.IO for real-time progress
      const socketConnection = io('/upload');
      setSocket(socketConnection);

      socketConnection.on('upload-progress', (progress: number) => {
        setUploadProgress(progress);
      });

      socketConnection.on('processing-started', () => {
        console.log('Video processing started');
      });

      socketConnection.on('processing-complete', (result: any) => {
        console.log('Video processing complete:', result);
        setIsUploading(false);
        socketConnection.disconnect();
      });

      socketConnection.on('error', (error: string) => {
        setUploadError(error);
        setIsUploading(false);
        socketConnection.disconnect();
      });

      // Start upload with XMLHttpRequest for progress tracking
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const uploadPercent = (e.loaded / e.total) * 50; // Upload is 50% of total progress
          setUploadProgress(uploadPercent);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          setUploadProgress(50); // Upload complete, processing starts
          return response;
        } else {
          throw new Error(`Upload failed: ${xhr.statusText}`);
        }
      });

      xhr.addEventListener('error', () => {
        throw new Error('Upload failed due to network error');
      });

      xhr.open('POST', '/api/upload/webcam');
      xhr.send(formData);

      return new Promise((resolve, reject) => {
        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error(`Upload failed: ${xhr.statusText}`));
          }
        });
        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed'));
        });
      });

    } catch (error: any) {
      setUploadError(error.message);
      setIsUploading(false);
      throw error;
    }
  }, []);

  return {
    uploadFile,
    uploadProgress,
    isUploading,
    uploadError
  };
};
```

---

## Backend Implementation

### Upload Handler (`server/routes/upload.js`)

```javascript
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const ffmpeg = require('fluent-ffmpeg');
const { v4: uuidv4 } = require('uuid');
const router = express.Router();

// Configure multer for video uploads
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = path.join(__dirname, '../../uploads/webcam');
    await fs.mkdir(uploadDir, { recursive: true });
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueId = uuidv4();
    const extension = path.extname(file.originalname) || '.webm';
    cb(null, `webcam-${uniqueId}${extension}`);
  }
});

const upload = multer({
  storage,
  limits: {
    fileSize: 2 * 1024 * 1024 * 1024, // 2GB limit
    fieldSize: 10 * 1024 * 1024 // 10MB metadata limit
  },
  fileFilter: (req, file, cb) => {
    const allowedMimes = [
      'video/webm',
      'video/mp4',
      'video/quicktime',
      'video/x-msvideo'
    ];

    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only video files are allowed.'));
    }
  }
});

// Webcam upload endpoint
router.post('/webcam', upload.single('video'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No video file provided' });
    }

    const metadata = JSON.parse(req.body.metadata);
    const videoId = uuidv4();
    const inputPath = req.file.path;
    const outputPath = path.join(
      path.dirname(inputPath),
      `processed-${videoId}.mp4`
    );

    // Validate metadata
    const validationResult = validateMetadata(metadata);
    if (!validationResult.valid) {
      await fs.unlink(inputPath); // Clean up uploaded file
      return res.status(400).json({ error: validationResult.errors });
    }

    // Create database record
    const videoRecord = await createVideoRecord({
      id: videoId,
      originalFilename: req.file.filename,
      processedFilename: `processed-${videoId}.mp4`,
      metadata,
      uploadDate: new Date(),
      status: 'processing'
    });

    // Start video processing
    processVideo(inputPath, outputPath, metadata, req.io)
      .then(async (result) => {
        // Update database with processing results
        await updateVideoRecord(videoId, {
          status: 'completed',
          duration: result.duration,
          fileSize: result.fileSize,
          processingCompletedAt: new Date()
        });

        // Queue for SharkTrack analysis
        await queueForAnalysis(videoId, outputPath, metadata);

        req.io.emit('processing-complete', {
          videoId,
          status: 'completed',
          result
        });
      })
      .catch(async (error) => {
        console.error('Video processing failed:', error);

        await updateVideoRecord(videoId, {
          status: 'failed',
          errorMessage: error.message,
          processingFailedAt: new Date()
        });

        req.io.emit('error', `Processing failed: ${error.message}`);
      });

    res.json({
      success: true,
      videoId,
      message: 'Upload successful, processing started'
    });

  } catch (error) {
    console.error('Upload error:', error);

    if (req.file) {
      // Clean up uploaded file on error
      await fs.unlink(req.file.path).catch(console.error);
    }

    res.status(500).json({
      error: 'Upload failed',
      details: error.message
    });
  }
});

// Video processing function
async function processVideo(inputPath, outputPath, metadata, io) {
  return new Promise((resolve, reject) => {
    let totalDuration = 0;

    // First pass: get video information
    ffmpeg.ffprobe(inputPath, (err, probeData) => {
      if (err) {
        reject(new Error(`Failed to probe video: ${err.message}`));
        return;
      }

      totalDuration = probeData.format.duration;

      // Second pass: process video with metadata embedding
      const command = ffmpeg(inputPath)
        .outputOptions([
          '-c:v libx264',           // H.264 video codec
          '-preset medium',         // Encoding speed vs compression
          '-crf 23',               // Quality (18-28, lower is better)
          '-c:a aac',              // AAC audio codec
          '-movflags +faststart',   // Enable web streaming
          '-f mp4'                 // MP4 container
        ])
        // Embed GPS metadata if available
        .outputOptions(metadata.location ? [
          `-metadata location="${metadata.location.latitude},${metadata.location.longitude}"`,
          `-metadata gps_latitude="${metadata.location.latitude}"`,
          `-metadata gps_longitude="${metadata.location.longitude}"`,
          `-metadata gps_accuracy="${metadata.location.accuracy}"`
        ] : [])
        // Embed research metadata
        .outputOptions([
          `-metadata title="${metadata.title}"`,
          `-metadata description="${metadata.description}"`,
          `-metadata artist="${metadata.researcherName}"`,
          `-metadata album="${metadata.institution}"`,
          `-metadata date="${metadata.recordingDate}"`,
          `-metadata habitat="${metadata.habitat}"`
        ])
        // Add depth and environmental data if available
        .outputOptions(metadata.depth ? [`-metadata depth="${metadata.depth}m"`] : [])
        .outputOptions(metadata.temperature ? [`-metadata temperature="${metadata.temperature}°C"`] : [])
        .outputOptions(metadata.visibility ? [`-metadata visibility="${metadata.visibility}m"`] : []);

      command
        .on('start', (commandLine) => {
          console.log('FFmpeg started:', commandLine);
          io.emit('processing-started', { videoId: metadata.videoId });
        })
        .on('progress', (progress) => {
          const percentage = Math.round((progress.timemark / totalDuration) * 100);
          io.emit('upload-progress', Math.min(50 + percentage / 2, 100)); // 50-100% range
        })
        .on('end', async () => {
          try {
            const stats = await fs.stat(outputPath);
            resolve({
              duration: totalDuration,
              fileSize: stats.size,
              outputPath
            });
          } catch (error) {
            reject(error);
          }
        })
        .on('error', (error) => {
          reject(new Error(`FFmpeg processing failed: ${error.message}`));
        })
        .save(outputPath);
    });
  });
}

// Metadata validation
function validateMetadata(metadata) {
  const errors = [];

  if (!metadata.title || metadata.title.trim().length < 3) {
    errors.push('Title must be at least 3 characters long');
  }

  if (!metadata.researcherName || metadata.researcherName.trim().length < 2) {
    errors.push('Researcher name is required');
  }

  if (!metadata.institution || metadata.institution.trim().length < 2) {
    errors.push('Institution is required');
  }

  if (!metadata.habitat) {
    errors.push('Habitat type is required');
  }

  if (metadata.depth && (metadata.depth < 0 || metadata.depth > 11000)) {
    errors.push('Depth must be between 0 and 11000 meters');
  }

  if (metadata.temperature && (metadata.temperature < -2 || metadata.temperature > 40)) {
    errors.push('Temperature must be between -2°C and 40°C');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

// Database operations
async function createVideoRecord(data) {
  // Database integration would go here
  // For now, return mock data
  console.log('Creating video record:', data);
  return { id: data.id, ...data };
}

async function updateVideoRecord(videoId, updates) {
  // Database integration would go here
  console.log('Updating video record:', videoId, updates);
  return true;
}

async function queueForAnalysis(videoId, videoPath, metadata) {
  // Queue video for SharkTrack analysis
  console.log('Queuing for analysis:', videoId, videoPath);

  // This would integrate with the main SharkTrack processing queue
  // Could use Redis Queue, Bull, or direct API call

  return true;
}

module.exports = router;
```

### Socket.IO Integration (`server/socketHandlers/uploadHandler.js`)

```javascript
const { Server } = require('socket.io');

function setupUploadSocketHandlers(io) {
  const uploadNamespace = io.of('/upload');

  uploadNamespace.on('connection', (socket) => {
    console.log('Upload client connected:', socket.id);

    socket.on('disconnect', () => {
      console.log('Upload client disconnected:', socket.id);
    });

    // Handle upload cancellation
    socket.on('cancel-upload', (data) => {
      console.log('Upload cancelled:', data);
      // Implement upload cancellation logic
    });

    // Handle processing status requests
    socket.on('get-status', async (videoId) => {
      try {
        const status = await getVideoProcessingStatus(videoId);
        socket.emit('status-update', status);
      } catch (error) {
        socket.emit('error', 'Failed to get status');
      }
    });
  });

  return uploadNamespace;
}

async function getVideoProcessingStatus(videoId) {
  // Query database for video processing status
  // Return current status, progress, etc.
  return {
    videoId,
    status: 'processing',
    progress: 75,
    estimatedCompletion: new Date(Date.now() + 300000) // 5 minutes
  };
}

module.exports = { setupUploadSocketHandlers };
```

---

## GPS Integration and Metadata Handling

### Enhanced GPS Component (`components/GPSTracker.tsx`)

```typescript
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';

interface GPSTrackerProps {
  onLocationUpdate: (coordinates: GPSCoordinates) => void;
  showMap?: boolean;
  autoTrack?: boolean;
}

export const GPSTracker: React.FC<GPSTrackerProps> = ({
  onLocationUpdate,
  showMap = true,
  autoTrack = false
}) => {
  const [position, setPosition] = useState<[number, number] | null>(null);
  const [accuracy, setAccuracy] = useState<number>(0);
  const [isTracking, setIsTracking] = useState(false);
  const [watchId, setWatchId] = useState<number | null>(null);

  useEffect(() => {
    if (autoTrack) {
      startTracking();
    }
    return () => {
      stopTracking();
    };
  }, [autoTrack]);

  const startTracking = () => {
    if (!navigator.geolocation) return;

    const options: PositionOptions = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 30000
    };

    const id = navigator.geolocation.watchPosition(
      (pos) => {
        const coords: [number, number] = [
          pos.coords.latitude,
          pos.coords.longitude
        ];
        setPosition(coords);
        setAccuracy(pos.coords.accuracy);

        const gpsData: GPSCoordinates = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          timestamp: pos.timestamp,
          source: pos.coords.accuracy < 100 ? 'gps' : 'network'
        };

        onLocationUpdate(gpsData);
      },
      (error) => {
        console.error('GPS tracking error:', error);
      },
      options
    );

    setWatchId(id);
    setIsTracking(true);
  };

  const stopTracking = () => {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      setWatchId(null);
      setIsTracking(false);
    }
  };

  const getCurrentLocation = () => {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords: [number, number] = [
          pos.coords.latitude,
          pos.coords.longitude
        ];
        setPosition(coords);
        setAccuracy(pos.coords.accuracy);

        const gpsData: GPSCoordinates = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          timestamp: pos.timestamp,
          source: pos.coords.accuracy < 100 ? 'gps' : 'network'
        };

        onLocationUpdate(gpsData);
      },
      (error) => {
        console.error('Location error:', error);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    );
  };

  return (
    <div className="gps-tracker">
      <div className="gps-controls">
        <button onClick={getCurrentLocation}>
          📍 Get Current Location
        </button>

        <button
          onClick={isTracking ? stopTracking : startTracking}
          className={isTracking ? 'tracking' : ''}
        >
          {isTracking ? '⏹️ Stop Tracking' : '▶️ Start Tracking'}
        </button>
      </div>

      {position && (
        <div className="location-info">
          <p><strong>Coordinates:</strong></p>
          <p>Lat: {position[0].toFixed(6)}</p>
          <p>Lng: {position[1].toFixed(6)}</p>
          <p>Accuracy: ±{accuracy.toFixed(0)}m</p>
        </div>
      )}

      {showMap && position && (
        <div className="location-map">
          <MapContainer
            center={position}
            zoom={15}
            style={{ height: '300px', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />
            <Marker position={position}>
              <Popup>
                Recording Location<br/>
                Accuracy: ±{accuracy.toFixed(0)}m
              </Popup>
            </Marker>
          </MapContainer>
        </div>
      )}
    </div>
  );
};
```

### Metadata Form Component (`components/MetadataForm.tsx`)

```typescript
import React, { useState } from 'react';
import { GPSTracker } from './GPSTracker';

interface MetadataFormProps {
  videoBlob: Blob | null;
  duration: number;
  location: GPSCoordinates | null;
  onSubmit: (metadata: VideoMetadata) => void;
  onCancel: () => void;
}

export const MetadataForm: React.FC<MetadataFormProps> = ({
  videoBlob,
  duration,
  location,
  onSubmit,
  onCancel
}) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    researcherName: '',
    institution: '',
    habitat: '',
    depth: '',
    temperature: '',
    visibility: '',
    notes: ''
  });

  const [currentLocation, setCurrentLocation] = useState<GPSCoordinates | null>(location);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (videoBlob) {
      const url = URL.createObjectURL(videoBlob);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [videoBlob]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const metadata: VideoMetadata = {
      ...formData,
      depth: formData.depth ? parseFloat(formData.depth) : undefined,
      temperature: formData.temperature ? parseFloat(formData.temperature) : undefined,
      visibility: formData.visibility ? parseFloat(formData.visibility) : undefined,
      location: currentLocation,
      duration,
      recordingDate: new Date().toISOString(),
      deviceInfo: {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language
      }
    };

    onSubmit(metadata);
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="metadata-form">
      <h2>Add Video Metadata</h2>

      <div className="form-layout">
        <div className="preview-section">
          {previewUrl && (
            <div className="video-preview">
              <video
                src={previewUrl}
                controls
                style={{ width: '100%', maxHeight: '300px' }}
              />
              <div className="video-info">
                <p>Duration: {formatDuration(duration)}</p>
                <p>Size: {videoBlob ? (videoBlob.size / 1024 / 1024).toFixed(2) : 0} MB</p>
              </div>
            </div>
          )}

          <GPSTracker
            onLocationUpdate={setCurrentLocation}
            showMap={true}
            autoTrack={false}
          />
        </div>

        <div className="form-section">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="title">Video Title *</label>
              <input
                type="text"
                id="title"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                required
                placeholder="e.g., Reef sharks at North Point"
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                placeholder="Brief description of what was observed..."
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="researcherName">Researcher Name *</label>
                <input
                  type="text"
                  id="researcherName"
                  value={formData.researcherName}
                  onChange={(e) => setFormData(prev => ({ ...prev, researcherName: e.target.value }))}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="institution">Institution *</label>
                <input
                  type="text"
                  id="institution"
                  value={formData.institution}
                  onChange={(e) => setFormData(prev => ({ ...prev, institution: e.target.value }))}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="habitat">Habitat Type *</label>
              <select
                id="habitat"
                value={formData.habitat}
                onChange={(e) => setFormData(prev => ({ ...prev, habitat: e.target.value }))}
                required
              >
                <option value="">Select habitat...</option>
                <option value="coral_reef">Coral Reef</option>
                <option value="rocky_reef">Rocky Reef</option>
                <option value="sandy_bottom">Sandy Bottom</option>
                <option value="seagrass">Seagrass Beds</option>
                <option value="kelp_forest">Kelp Forest</option>
                <option value="open_ocean">Open Ocean</option>
                <option value="seamount">Seamount</option>
                <option value="coastal">Coastal Waters</option>
                <option value="estuarine">Estuarine</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="depth">Depth (meters)</label>
                <input
                  type="number"
                  id="depth"
                  value={formData.depth}
                  onChange={(e) => setFormData(prev => ({ ...prev, depth: e.target.value }))}
                  min="0"
                  max="11000"
                  step="0.1"
                  placeholder="e.g., 15.5"
                />
              </div>

              <div className="form-group">
                <label htmlFor="temperature">Water Temperature (°C)</label>
                <input
                  type="number"
                  id="temperature"
                  value={formData.temperature}
                  onChange={(e) => setFormData(prev => ({ ...prev, temperature: e.target.value }))}
                  min="-2"
                  max="40"
                  step="0.1"
                  placeholder="e.g., 24.5"
                />
              </div>

              <div className="form-group">
                <label htmlFor="visibility">Visibility (meters)</label>
                <input
                  type="number"
                  id="visibility"
                  value={formData.visibility}
                  onChange={(e) => setFormData(prev => ({ ...prev, visibility: e.target.value }))}
                  min="0"
                  max="100"
                  step="0.1"
                  placeholder="e.g., 30"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="notes">Additional Notes</label>
              <textarea
                id="notes"
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                rows={3}
                placeholder="Any additional observations or notes..."
              />
            </div>

            <div className="location-summary">
              <h4>Location Information</h4>
              {currentLocation ? (
                <div className="location-details">
                  <p>📍 {currentLocation.latitude.toFixed(6)}, {currentLocation.longitude.toFixed(6)}</p>
                  <p>Accuracy: ±{currentLocation.accuracy}m</p>
                  <p>Source: {currentLocation.source.toUpperCase()}</p>
                </div>
              ) : (
                <p className="no-location">⚠️ No location data available</p>
              )}
            </div>

            <div className="form-actions">
              <button type="button" onClick={onCancel} className="btn-secondary">
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                Upload Video
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
```

---

## Security and Privacy Considerations

### Data Protection
- **HTTPS Only**: All camera and GPS data transmission encrypted
- **Local Processing**: Video preview and metadata handled client-side when possible
- **Automatic Cleanup**: Temporary files removed after processing
- **Access Control**: Optional researcher authentication for data attribution

### Privacy Features
- **Location Opt-out**: Users can manually disable GPS or provide approximate location
- **Data Anonymisation**: Option to remove or generalise location data
- **Consent Management**: Clear consent for camera and location access
- **Data Retention**: Configurable retention policies for uploaded data

### Error Handling and Fallbacks
- **Camera Fallback**: File upload option when camera access fails
- **Location Fallback**: Manual location entry or IP-based approximation
- **Upload Resume**: Automatic retry and resume for failed uploads
- **Offline Support**: Local storage with sync when connection restored

---

## Integration with SharkTrack Processing

### Processing Queue Integration
```javascript
// Queue management for video processing
const Queue = require('bull');
const videoProcessingQueue = new Queue('video processing');

videoProcessingQueue.process(async (job) => {
  const { videoPath, metadata, videoId } = job.data;

  // Run SharkTrack analysis
  const sharktrackResults = await runSharkTrackAnalysis(videoPath, {
    mode: 'analyst', // Full tracking mode
    confidence: 0.25,
    output: `/tmp/sharktrack-${videoId}`
  });

  // Store results in database
  await storeAnalysisResults(videoId, sharktrackResults);

  // Notify user of completion
  io.emit('analysis-complete', {
    videoId,
    results: sharktrackResults
  });

  return sharktrackResults;
});

async function runSharkTrackAnalysis(videoPath, options) {
  // Integration with main SharkTrack processing
  // This would call the existing app.py or use the Python API
  const { spawn } = require('child_process');

  return new Promise((resolve, reject) => {
    const sharktrack = spawn('python', [
      'app.py',
      '--input', videoPath,
      '--output', options.output,
      '--conf', options.confidence.toString()
    ]);

    let output = '';
    sharktrack.stdout.on('data', (data) => {
      output += data.toString();
    });

    sharktrack.on('close', (code) => {
      if (code === 0) {
        // Parse SharkTrack results
        resolve(parseSharkTrackOutput(options.output));
      } else {
        reject(new Error(`SharkTrack processing failed with code ${code}`));
      }
    });
  });
}
```

This webcam upload portal provides a complete solution for point-and-shoot marine video data collection with comprehensive metadata handling, real-time processing feedback, and seamless integration with the SharkTrack analysis pipeline.