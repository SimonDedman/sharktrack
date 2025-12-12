# Mobile Applications for SharkTrack Platform

This document specifies the complete mobile application suite for Android and iOS, enabling field researchers to upload data, view statistics, and access the global marine research network from mobile devices.

## Application Suite Overview

### Core Applications
1. **SharkTrack Field** - Primary data collection and upload app
2. **SharkTrack Analytics** - Research statistics and collaboration dashboard
3. **SharkTrack Viewer** - Video playback and annotation review

### Technology Stack
- **Android**: Kotlin with Jetpack Compose UI
- **iOS**: Swift with SwiftUI framework
- **Cross-Platform**: Shared networking and business logic
- **Backend Integration**: REST APIs with real-time WebSocket connections
- **Video Processing**: FFmpeg mobile libraries for on-device processing
- **Offline Support**: SQLite with sync capabilities
- **Authentication**: OAuth 2.0 with biometric authentication

### Application Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mobile Application Suite                     │
├─────────────────────────────────────────────────────────────────┤
│  SharkTrack Field (Data Collection)                            │
│  ├── Camera Integration      ├── GPS Tracking                  │
│  ├── Metadata Forms         ├── Offline Storage               │
│  ├── Upload Queue           └── Background Sync               │
├─────────────────────────────────────────────────────────────────┤
│  SharkTrack Analytics (Research Dashboard)                     │
│  ├── Personal Statistics    ├── Global Network Status         │
│  ├── Contribution Tracking  ├── Collaboration Tools           │
│  ├── Species Intelligence   └── Research Impact Metrics       │
├─────────────────────────────────────────────────────────────────┤
│  SharkTrack Viewer (Video & Annotation)                        │
│  ├── Video Streaming        ├── Detection Overlays            │
│  ├── Annotation Tools       ├── Collaborative Review          │
│  ├── Offline Downloads      └── Quality Assessment            │
├─────────────────────────────────────────────────────────────────┤
│  Shared Infrastructure                                         │
│  ├── Authentication Service ├── Data Synchronization          │
│  ├── Network Layer          ├── Local Database                │
│  ├── Blockchain Integration └── Push Notifications            │
└─────────────────────────────────────────────────────────────────┘
```

---

## SharkTrack Field - Data Collection App

### Android Implementation (Kotlin)

#### Main Activity (`MainActivity.kt`)

```kotlin
package org.sharktrack.field

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dagger.hilt.android.AndroidEntryPoint
import org.sharktrack.field.ui.navigation.SharkTrackNavigation
import org.sharktrack.field.ui.theme.SharkTrackTheme
import org.sharktrack.field.viewmodel.MainViewModel

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    private val viewModel: MainViewModel by viewModels()

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        viewModel.onPermissionsResult(permissions)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request necessary permissions
        requestPermissions()

        setContent {
            SharkTrackTheme {
                val uiState by viewModel.uiState.collectAsStateWithLifecycle()

                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    when {
                        uiState.isLoading -> LoadingScreen()
                        !uiState.hasRequiredPermissions -> PermissionScreen {
                            requestPermissions()
                        }
                        !uiState.isAuthenticated -> AuthenticationScreen()
                        else -> SharkTrackNavigation()
                    }
                }
            }
        }
    }

    private fun requestPermissions() {
        val requiredPermissions = arrayOf(
            Manifest.permission.CAMERA,
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.WRITE_EXTERNAL_STORAGE,
            Manifest.permission.READ_EXTERNAL_STORAGE
        )

        val missingPermissions = requiredPermissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missingPermissions.isNotEmpty()) {
            permissionLauncher.launch(missingPermissions.toTypedArray())
        } else {
            viewModel.onPermissionsGranted()
        }
    }
}

@Composable
fun LoadingScreen() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator()
            Spacer(modifier = Modifier.height(16.dp))
            Text("Initializing SharkTrack...")
        }
    }
}

@Composable
fun PermissionScreen(onRequestPermissions: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Default.CameraAlt,
            contentDescription = "Camera Permission",
            modifier = Modifier.size(64.dp)
        )

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = "Camera and Location Access Required",
            style = MaterialTheme.typography.headlineSmall
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "SharkTrack needs camera and GPS access to record marine videos with location data.",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(24.dp))

        Button(onClick = onRequestPermissions) {
            Text("Grant Permissions")
        }
    }
}
```

#### Camera Recording Screen (`CameraRecordingScreen.kt`)

```kotlin
package org.sharktrack.field.ui.screens

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.video.*
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.sharktrack.field.viewmodel.CameraViewModel
import java.io.File
import java.text.SimpleDateFormat
import java.util.*
import kotlin.time.Duration.Companion.seconds

@SuppressLint("MissingPermission")
@Composable
fun CameraRecordingScreen(
    viewModel: CameraViewModel = hiltViewModel(),
    onNavigateToMetadata: (String) -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    var previewView by remember { mutableStateOf<PreviewView?>(null) }

    LaunchedEffect(Unit) {
        viewModel.startLocationUpdates()
    }

    Box(modifier = Modifier.fillMaxSize()) {
        // Camera Preview
        AndroidView(
            factory = { ctx ->
                PreviewView(ctx).apply {
                    previewView = this
                    scaleType = PreviewView.ScaleType.FILL_CENTER
                }
            },
            modifier = Modifier.fillMaxSize()
        ) { preview ->
            val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
            cameraProviderFuture.addListener({
                val cameraProvider = cameraProviderFuture.get()

                val previewUseCase = Preview.Builder()
                    .setTargetAspectRatio(AspectRatio.RATIO_16_9)
                    .build()
                    .also { it.setSurfaceProvider(preview.surfaceProvider) }

                val videoCapture = VideoCapture.withOutput(
                    FileOutputOptions.Builder(
                        File(context.getExternalFilesDir(null), "recording_${System.currentTimeMillis()}.mp4")
                    ).build()
                )

                val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

                try {
                    cameraProvider.unbindAll()
                    cameraProvider.bindToLifecycle(
                        lifecycleOwner,
                        cameraSelector,
                        previewUseCase,
                        videoCapture
                    )

                    viewModel.setCameraProvider(cameraProvider, videoCapture)
                } catch (exc: Exception) {
                    viewModel.onCameraError(exc.message ?: "Camera initialization failed")
                }
            }, ContextCompat.getMainExecutor(context))
        }

        // Recording UI Overlay
        RecordingOverlay(
            uiState = uiState,
            onStartRecording = { viewModel.startRecording() },
            onStopRecording = { viewModel.stopRecording() },
            onSwitchCamera = { viewModel.switchCamera() },
            onToggleFlash = { viewModel.toggleFlash() },
            modifier = Modifier.align(Alignment.BottomCenter)
        )

        // Top Status Bar
        TopStatusBar(
            uiState = uiState,
            modifier = Modifier.align(Alignment.TopCenter)
        )

        // Recording completed dialog
        if (uiState.recordingCompleted != null) {
            RecordingCompletedDialog(
                videoPath = uiState.recordingCompleted,
                onNavigateToMetadata = onNavigateToMetadata,
                onDismiss = { viewModel.clearRecordingCompleted() }
            )
        }
    }
}

@Composable
fun RecordingOverlay(
    uiState: CameraUiState,
    onStartRecording: () -> Unit,
    onStopRecording: () -> Unit,
    onSwitchCamera: () -> Unit,
    onToggleFlash: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(32.dp),
        horizontalArrangement = Arrangement.SpaceEvenly,
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Flash toggle
        IconButton(
            onClick = onToggleFlash,
            modifier = Modifier
                .size(48.dp)
                .background(
                    color = if (uiState.isFlashOn) Color.Yellow else Color.Black.copy(alpha = 0.5f),
                    shape = CircleShape
                )
        ) {
            Icon(
                imageVector = if (uiState.isFlashOn) Icons.Default.FlashOn else Icons.Default.FlashOff,
                contentDescription = "Flash",
                tint = Color.White
            )
        }

        // Record button
        Button(
            onClick = if (uiState.isRecording) onStopRecording else onStartRecording,
            modifier = Modifier.size(72.dp),
            shape = CircleShape,
            colors = ButtonDefaults.buttonColors(
                containerColor = if (uiState.isRecording) Color.Red else Color.White
            )
        ) {
            Icon(
                imageVector = if (uiState.isRecording) Icons.Default.Stop else Icons.Default.VideoCall,
                contentDescription = if (uiState.isRecording) "Stop Recording" else "Start Recording",
                tint = if (uiState.isRecording) Color.White else Color.Red,
                modifier = Modifier.size(32.dp)
            )
        }

        // Camera switch
        IconButton(
            onClick = onSwitchCamera,
            modifier = Modifier
                .size(48.dp)
                .background(
                    color = Color.Black.copy(alpha = 0.5f),
                    shape = CircleShape
                )
        ) {
            Icon(
                imageVector = Icons.Default.SwitchCamera,
                contentDescription = "Switch Camera",
                tint = Color.White
            )
        }
    }
}

@Composable
fun TopStatusBar(
    uiState: CameraUiState,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        color = Color.Black.copy(alpha = 0.7f),
        shape = MaterialTheme.shapes.medium
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Recording duration
            if (uiState.isRecording) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .background(Color.Red, CircleShape)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = formatDuration(uiState.recordingDuration),
                        style = MaterialTheme.typography.labelLarge,
                        color = Color.White
                    )
                }
            } else {
                Text(
                    text = "Ready to Record",
                    style = MaterialTheme.typography.labelLarge,
                    color = Color.White
                )
            }

            // GPS Status
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = if (uiState.hasGpsLock) Icons.Default.GpsFixed else Icons.Default.GpsNotFixed,
                    contentDescription = "GPS Status",
                    tint = if (uiState.hasGpsLock) Color.Green else Color.Red,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(modifier = Modifier.width(4.dp))
                Text(
                    text = if (uiState.hasGpsLock) "GPS: ±${uiState.gpsAccuracy}m" else "No GPS",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White
                )
            }
        }
    }
}

@Composable
fun RecordingCompletedDialog(
    videoPath: String,
    onNavigateToMetadata: (String) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Recording Complete") },
        text = { Text("Video recorded successfully. Add metadata to upload?") },
        confirmButton = {
            TextButton(onClick = { onNavigateToMetadata(videoPath) }) {
                Text("Add Metadata")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Record Another")
            }
        }
    )
}

private fun formatDuration(seconds: Int): String {
    val minutes = seconds / 60
    val remainingSeconds = seconds % 60
    return String.format("%02d:%02d", minutes, remainingSeconds)
}
```

#### Video Metadata Form (`VideoMetadataScreen.kt`)

```kotlin
package org.sharktrack.field.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.sharktrack.field.model.VideoMetadata
import org.sharktrack.field.viewmodel.MetadataViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VideoMetadataScreen(
    videoPath: String,
    viewModel: MetadataViewModel = hiltViewModel(),
    onUploadStarted: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(videoPath) {
        viewModel.loadVideoInfo(videoPath)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "Video Metadata",
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        // Video Info Card
        VideoInfoCard(
            uiState = uiState,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        // Research Information
        ResearchInfoSection(
            uiState = uiState,
            onUpdateMetadata = viewModel::updateMetadata,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        // Environmental Data
        EnvironmentalDataSection(
            uiState = uiState,
            onUpdateMetadata = viewModel::updateMetadata,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        // Location Information
        LocationInfoSection(
            uiState = uiState,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        // Upload Button
        Button(
            onClick = {
                viewModel.uploadVideo()
                onUploadStarted()
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            enabled = uiState.isFormValid && !uiState.isUploading
        ) {
            if (uiState.isUploading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Uploading...")
            } else {
                Icon(
                    imageVector = Icons.Default.CloudUpload,
                    contentDescription = "Upload"
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Upload Video")
            }
        }
    }
}

@Composable
fun VideoInfoCard(
    uiState: MetadataUiState,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "Video Information",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(bottom = 8.dp)
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                InfoItem(
                    label = "Duration",
                    value = formatDuration(uiState.videoDuration)
                )
                InfoItem(
                    label = "Size",
                    value = formatFileSize(uiState.videoSize)
                )
                InfoItem(
                    label = "Resolution",
                    value = "${uiState.videoWidth}×${uiState.videoHeight}"
                )
            }
        }
    }
}

@Composable
fun ResearchInfoSection(
    uiState: MetadataUiState,
    onUpdateMetadata: (VideoMetadata) -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "Research Information",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            OutlinedTextField(
                value = uiState.metadata.title,
                onValueChange = { onUpdateMetadata(uiState.metadata.copy(title = it)) },
                label = { Text("Video Title") },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
                singleLine = true
            )

            OutlinedTextField(
                value = uiState.metadata.description,
                onValueChange = { onUpdateMetadata(uiState.metadata.copy(description = it)) },
                label = { Text("Description") },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
                minLines = 3,
                maxLines = 5
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedTextField(
                    value = uiState.metadata.researcherName,
                    onValueChange = { onUpdateMetadata(uiState.metadata.copy(researcherName = it)) },
                    label = { Text("Researcher") },
                    modifier = Modifier.weight(1f),
                    singleLine = true
                )

                OutlinedTextField(
                    value = uiState.metadata.institution,
                    onValueChange = { onUpdateMetadata(uiState.metadata.copy(institution = it)) },
                    label = { Text("Institution") },
                    modifier = Modifier.weight(1f),
                    singleLine = true
                )
            }
        }
    }
}

@Composable
fun EnvironmentalDataSection(
    uiState: MetadataUiState,
    onUpdateMetadata: (VideoMetadata) -> Unit,
    modifier: Modifier = Modifier
) {
    var expandedHabitat by remember { mutableStateOf(false) }

    Card(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "Environmental Data",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            // Habitat Dropdown
            ExposedDropdownMenuBox(
                expanded = expandedHabitat,
                onExpandedChange = { expandedHabitat = !expandedHabitat }
            ) {
                OutlinedTextField(
                    value = uiState.metadata.habitat,
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Habitat Type") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expandedHabitat) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .menuAnchor()
                        .padding(bottom = 8.dp)
                )

                ExposedDropdownMenu(
                    expanded = expandedHabitat,
                    onDismissRequest = { expandedHabitat = false }
                ) {
                    val habitats = listOf(
                        "Coral Reef", "Rocky Reef", "Sandy Bottom", "Seagrass Beds",
                        "Kelp Forest", "Open Ocean", "Seamount", "Coastal Waters",
                        "Estuarine", "Other"
                    )

                    habitats.forEach { habitat ->
                        DropdownMenuItem(
                            text = { Text(habitat) },
                            onClick = {
                                onUpdateMetadata(uiState.metadata.copy(habitat = habitat))
                                expandedHabitat = false
                            }
                        )
                    }
                }
            }

            // Environmental parameters
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedTextField(
                    value = uiState.metadata.depth?.toString() ?: "",
                    onValueChange = {
                        val depth = it.toDoubleOrNull()
                        onUpdateMetadata(uiState.metadata.copy(depth = depth))
                    },
                    label = { Text("Depth (m)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.weight(1f),
                    singleLine = true
                )

                OutlinedTextField(
                    value = uiState.metadata.temperature?.toString() ?: "",
                    onValueChange = {
                        val temp = it.toDoubleOrNull()
                        onUpdateMetadata(uiState.metadata.copy(temperature = temp))
                    },
                    label = { Text("Temp (°C)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.weight(1f),
                    singleLine = true
                )

                OutlinedTextField(
                    value = uiState.metadata.visibility?.toString() ?: "",
                    onValueChange = {
                        val vis = it.toDoubleOrNull()
                        onUpdateMetadata(uiState.metadata.copy(visibility = vis))
                    },
                    label = { Text("Visibility (m)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.weight(1f),
                    singleLine = true
                )
            }
        }
    }
}

@Composable
fun LocationInfoSection(
    uiState: MetadataUiState,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "Location Information",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            if (uiState.location != null) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    InfoItem(
                        label = "Latitude",
                        value = "%.6f".format(uiState.location.latitude)
                    )
                    InfoItem(
                        label = "Longitude",
                        value = "%.6f".format(uiState.location.longitude)
                    )
                    InfoItem(
                        label = "Accuracy",
                        value = "±${uiState.location.accuracy}m"
                    )
                }
            } else {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.GpsOff,
                        contentDescription = "No GPS",
                        tint = MaterialTheme.colorScheme.error
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Location data not available",
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }
        }
    }
}

@Composable
fun InfoItem(
    label: String,
    value: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium
        )
    }
}

private fun formatDuration(milliseconds: Long): String {
    val seconds = milliseconds / 1000
    val minutes = seconds / 60
    val hours = minutes / 60

    return when {
        hours > 0 -> String.format("%d:%02d:%02d", hours, minutes % 60, seconds % 60)
        else -> String.format("%02d:%02d", minutes, seconds % 60)
    }
}

private fun formatFileSize(bytes: Long): String {
    val units = arrayOf("B", "KB", "MB", "GB")
    var size = bytes.toDouble()
    var unitIndex = 0

    while (size >= 1024 && unitIndex < units.size - 1) {
        size /= 1024
        unitIndex++
    }

    return "%.1f %s".format(size, units[unitIndex])
}
```

---

## iOS Implementation (Swift)

### Main App Structure (`SharkTrackFieldApp.swift`)

```swift
import SwiftUI
import AVFoundation
import CoreLocation

@main
struct SharkTrackFieldApp: App {
    @StateObject private var appState = AppState()
    @StateObject private var authManager = AuthenticationManager()
    @StateObject private var locationManager = LocationManager()
    @StateObject private var uploadManager = UploadManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .environmentObject(authManager)
                .environmentObject(locationManager)
                .environmentObject(uploadManager)
                .onAppear {
                    requestPermissions()
                }
        }
    }

    private func requestPermissions() {
        // Request camera permission
        AVCaptureDevice.requestAccess(for: .video) { granted in
            DispatchQueue.main.async {
                appState.cameraPermissionGranted = granted
            }
        }

        // Request microphone permission
        AVCaptureDevice.requestAccess(for: .audio) { granted in
            DispatchQueue.main.async {
                appState.microphonePermissionGranted = granted
            }
        }

        // Request location permission
        locationManager.requestLocationPermission()
    }
}

class AppState: ObservableObject {
    @Published var cameraPermissionGranted = false
    @Published var microphonePermissionGranted = false
    @Published var locationPermissionGranted = false
    @Published var isAuthenticated = false
    @Published var currentUser: User?

    var hasAllPermissions: Bool {
        return cameraPermissionGranted && microphonePermissionGranted && locationPermissionGranted
    }
}
```

### Camera Recording View (`CameraRecordingView.swift`)

```swift
import SwiftUI
import AVFoundation
import CoreLocation

struct CameraRecordingView: View {
    @StateObject private var cameraManager = CameraManager()
    @EnvironmentObject var locationManager: LocationManager
    @State private var showingMetadataForm = false
    @State private var recordedVideoURL: URL?

    var body: some View {
        ZStack {
            // Camera Preview
            CameraPreviewView(cameraManager: cameraManager)
                .edgesIgnoringSafeArea(.all)

            VStack {
                // Top Status Bar
                TopStatusBar(
                    isRecording: cameraManager.isRecording,
                    recordingDuration: cameraManager.recordingDuration,
                    hasGPSLock: locationManager.hasAccurateLocation,
                    gpsAccuracy: locationManager.currentLocation?.horizontalAccuracy ?? 0
                )
                .padding(.top, 50)

                Spacer()

                // Recording Controls
                RecordingControls(
                    isRecording: cameraManager.isRecording,
                    isFlashOn: cameraManager.isFlashOn,
                    onStartRecording: { cameraManager.startRecording() },
                    onStopRecording: { cameraManager.stopRecording() },
                    onToggleFlash: { cameraManager.toggleFlash() },
                    onSwitchCamera: { cameraManager.switchCamera() }
                )
                .padding(.bottom, 50)
            }
        }
        .onAppear {
            cameraManager.setupCamera()
            locationManager.startLocationUpdates()
        }
        .onDisappear {
            cameraManager.stopRecording()
            locationManager.stopLocationUpdates()
        }
        .onChange(of: cameraManager.recordingComplete) { complete in
            if complete, let url = cameraManager.lastRecordingURL {
                recordedVideoURL = url
                showingMetadataForm = true
                cameraManager.recordingComplete = false
            }
        }
        .sheet(isPresented: $showingMetadataForm) {
            if let videoURL = recordedVideoURL {
                VideoMetadataFormView(
                    videoURL: videoURL,
                    location: locationManager.currentLocation
                )
            }
        }
    }
}

struct CameraPreviewView: UIViewRepresentable {
    let cameraManager: CameraManager

    func makeUIView(context: Context) -> UIView {
        let view = UIView(frame: UIScreen.main.bounds)

        cameraManager.previewLayer?.frame = view.frame
        cameraManager.previewLayer?.videoGravity = .resizeAspectFill

        if let previewLayer = cameraManager.previewLayer {
            view.layer.addSublayer(previewLayer)
        }

        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        cameraManager.previewLayer?.frame = uiView.frame
    }
}

struct TopStatusBar: View {
    let isRecording: Bool
    let recordingDuration: TimeInterval
    let hasGPSLock: Bool
    let gpsAccuracy: CLLocationAccuracy

    var body: some View {
        HStack {
            // Recording status
            HStack {
                if isRecording {
                    Circle()
                        .fill(Color.red)
                        .frame(width: 8, height: 8)
                        .animation(.easeInOut(duration: 1).repeatForever(), value: isRecording)

                    Text(formatDuration(recordingDuration))
                        .foregroundColor(.white)
                        .font(.system(.body, design: .monospaced))
                } else {
                    Text("Ready to Record")
                        .foregroundColor(.white)
                }
            }

            Spacer()

            // GPS status
            HStack {
                Image(systemName: hasGPSLock ? "location.fill" : "location.slash")
                    .foregroundColor(hasGPSLock ? .green : .red)

                if hasGPSLock {
                    Text("±\(Int(gpsAccuracy))m")
                        .foregroundColor(.white)
                        .font(.caption)
                } else {
                    Text("No GPS")
                        .foregroundColor(.red)
                        .font(.caption)
                }
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.black.opacity(0.7))
        )
        .padding(.horizontal, 16)
    }
}

struct RecordingControls: View {
    let isRecording: Bool
    let isFlashOn: Bool
    let onStartRecording: () -> Void
    let onStopRecording: () -> Void
    let onToggleFlash: () -> Void
    let onSwitchCamera: () -> Void

    var body: some View {
        HStack(spacing: 60) {
            // Flash toggle
            Button(action: onToggleFlash) {
                Image(systemName: isFlashOn ? "flashlight.on.fill" : "flashlight.off.fill")
                    .font(.title2)
                    .foregroundColor(.white)
                    .frame(width: 50, height: 50)
                    .background(
                        Circle()
                            .fill(isFlashOn ? Color.yellow : Color.black.opacity(0.5))
                    )
            }

            // Record button
            Button(action: isRecording ? onStopRecording : onStartRecording) {
                ZStack {
                    Circle()
                        .fill(Color.white)
                        .frame(width: 80, height: 80)

                    if isRecording {
                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color.red)
                            .frame(width: 30, height: 30)
                    } else {
                        Circle()
                            .fill(Color.red)
                            .frame(width: 65, height: 65)
                    }
                }
            }
            .scaleEffect(isRecording ? 0.9 : 1.0)
            .animation(.easeInOut(duration: 0.2), value: isRecording)

            // Camera switch
            Button(action: onSwitchCamera) {
                Image(systemName: "camera.rotate")
                    .font(.title2)
                    .foregroundColor(.white)
                    .frame(width: 50, height: 50)
                    .background(
                        Circle()
                            .fill(Color.black.opacity(0.5))
                    )
            }
        }
    }
}

private func formatDuration(_ duration: TimeInterval) -> String {
    let minutes = Int(duration) / 60
    let seconds = Int(duration) % 60
    return String(format: "%02d:%02d", minutes, seconds)
}
```

### Camera Manager (`CameraManager.swift`)

```swift
import AVFoundation
import UIKit
import CoreLocation

class CameraManager: NSObject, ObservableObject {
    @Published var isRecording = false
    @Published var recordingDuration: TimeInterval = 0
    @Published var isFlashOn = false
    @Published var recordingComplete = false
    @Published var lastRecordingURL: URL?

    private var captureSession: AVCaptureSession?
    private var videoOutput: AVCaptureMovieFileOutput?
    private var currentCamera: AVCaptureDevice?
    private var currentInput: AVCaptureDeviceInput?

    var previewLayer: AVCaptureVideoPreviewLayer?

    private var recordingTimer: Timer?
    private var recordingStartTime: Date?

    override init() {
        super.init()
    }

    func setupCamera() {
        let session = AVCaptureSession()
        session.sessionPreset = .high

        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
            print("Failed to get camera device")
            return
        }

        do {
            let input = try AVCaptureDeviceInput(device: camera)

            if session.canAddInput(input) {
                session.addInput(input)
                currentInput = input
                currentCamera = camera
            }

            // Add microphone input
            if let microphone = AVCaptureDevice.default(for: .audio) {
                let audioInput = try AVCaptureDeviceInput(device: microphone)
                if session.canAddInput(audioInput) {
                    session.addInput(audioInput)
                }
            }

            // Add video output
            let output = AVCaptureMovieFileOutput()
            if session.canAddOutput(output) {
                session.addOutput(output)
                videoOutput = output
            }

            previewLayer = AVCaptureVideoPreviewLayer(session: session)
            captureSession = session

            DispatchQueue.global(qos: .background).async {
                session.startRunning()
            }

        } catch {
            print("Error setting up camera: \(error)")
        }
    }

    func startRecording() {
        guard let videoOutput = videoOutput, !videoOutput.isRecording else { return }

        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let videoPath = documentsPath.appendingPathComponent("recording_\(Date().timeIntervalSince1970).mov")

        videoOutput.startRecording(to: videoPath, recordingDelegate: self)

        DispatchQueue.main.async {
            self.isRecording = true
            self.recordingStartTime = Date()
            self.startRecordingTimer()
        }
    }

    func stopRecording() {
        videoOutput?.stopRecording()

        DispatchQueue.main.async {
            self.isRecording = false
            self.stopRecordingTimer()
        }
    }

    func toggleFlash() {
        guard let camera = currentCamera, camera.hasTorch else { return }

        do {
            try camera.lockForConfiguration()

            if camera.torchMode == .off {
                camera.torchMode = .on
                isFlashOn = true
            } else {
                camera.torchMode = .off
                isFlashOn = false
            }

            camera.unlockForConfiguration()
        } catch {
            print("Error toggling flash: \(error)")
        }
    }

    func switchCamera() {
        guard let session = captureSession, let currentInput = currentInput else { return }

        session.beginConfiguration()
        session.removeInput(currentInput)

        let newPosition: AVCaptureDevice.Position = currentCamera?.position == .back ? .front : .back

        guard let newCamera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: newPosition) else {
            session.addInput(currentInput)
            session.commitConfiguration()
            return
        }

        do {
            let newInput = try AVCaptureDeviceInput(device: newCamera)

            if session.canAddInput(newInput) {
                session.addInput(newInput)
                self.currentInput = newInput
                self.currentCamera = newCamera
            } else {
                session.addInput(currentInput)
            }

            session.commitConfiguration()
        } catch {
            print("Error switching camera: \(error)")
            session.addInput(currentInput)
            session.commitConfiguration()
        }
    }

    private func startRecordingTimer() {
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            if let startTime = self.recordingStartTime {
                self.recordingDuration = Date().timeIntervalSince(startTime)
            }
        }
    }

    private func stopRecordingTimer() {
        recordingTimer?.invalidate()
        recordingTimer = nil
        recordingDuration = 0
    }
}

extension CameraManager: AVCaptureFileOutputRecordingDelegate {
    func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
        if let error = error {
            print("Recording error: \(error)")
        } else {
            DispatchQueue.main.async {
                self.lastRecordingURL = outputFileURL
                self.recordingComplete = true
            }
        }
    }
}
```

---

## SharkTrack Analytics - Research Dashboard App

### Analytics Dashboard (`AnalyticsDashboardView.swift`)

```swift
import SwiftUI
import Charts

struct AnalyticsDashboardView: View {
    @StateObject private var analyticsManager = AnalyticsManager()
    @State private var selectedTimeframe: Timeframe = .month

    enum Timeframe: String, CaseIterable {
        case week = "Week"
        case month = "Month"
        case year = "Year"
        case all = "All Time"
    }

    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    // Personal Statistics Header
                    PersonalStatsHeader(stats: analyticsManager.personalStats)

                    // Timeframe Selector
                    TimeframePicker(selectedTimeframe: $selectedTimeframe)
                        .onChange(of: selectedTimeframe) { newValue in
                            analyticsManager.loadData(for: newValue)
                        }

                    // Contribution Chart
                    ContributionChartCard(
                        data: analyticsManager.contributionData,
                        timeframe: selectedTimeframe
                    )

                    // Species Distribution
                    SpeciesDistributionCard(
                        speciesData: analyticsManager.speciesData
                    )

                    // Research Impact
                    ResearchImpactCard(
                        impactData: analyticsManager.impactData
                    )

                    // Global Network Status
                    GlobalNetworkCard(
                        networkData: analyticsManager.networkData
                    )

                    // Recent Activity
                    RecentActivityCard(
                        activities: analyticsManager.recentActivities
                    )
                }
                .padding()
            }
            .navigationTitle("Research Analytics")
            .refreshable {
                await analyticsManager.refreshData()
            }
        }
        .onAppear {
            analyticsManager.loadData(for: selectedTimeframe)
        }
    }
}

struct PersonalStatsHeader: View {
    let stats: PersonalStats

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                AsyncImage(url: URL(string: stats.avatarURL)) { image in
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                } placeholder: {
                    Circle()
                        .fill(Color.gray.opacity(0.3))
                }
                .frame(width: 60, height: 60)
                .clipShape(Circle())

                VStack(alignment: .leading, spacing: 4) {
                    Text(stats.researcherName)
                        .font(.title2)
                        .fontWeight(.bold)

                    Text(stats.institution)
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    HStack {
                        Image(systemName: "checkmark.seal.fill")
                            .foregroundColor(.blue)
                        Text("Verified Researcher")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 4) {
                    Text("\(stats.reputationScore)")
                        .font(.title)
                        .fontWeight(.bold)
                        .foregroundColor(.orange)

                    Text("Reputation")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            HStack(spacing: 20) {
                StatItem(
                    title: "Contributions",
                    value: "\(stats.totalContributions)",
                    icon: "square.and.arrow.up"
                )

                StatItem(
                    title: "SHARK Tokens",
                    value: String(format: "%.1f", stats.tokensEarned),
                    icon: "bitcoinsign.circle"
                )

                StatItem(
                    title: "Citations",
                    value: "\(stats.citations)",
                    icon: "quote.bubble"
                )

                StatItem(
                    title: "Collaborations",
                    value: "\(stats.collaborations)",
                    icon: "person.2"
                )
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(radius: 2)
        )
    }
}

struct ContributionChartCard: View {
    let data: [ContributionDataPoint]
    let timeframe: AnalyticsDashboardView.Timeframe

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Contributions Over Time")
                .font(.headline)
                .fontWeight(.semibold)

            Chart(data) { point in
                LineMark(
                    x: .value("Date", point.date),
                    y: .value("Count", point.count)
                )
                .foregroundStyle(.blue)
                .interpolationMethod(.catmullRom)

                AreaMark(
                    x: .value("Date", point.date),
                    y: .value("Count", point.count)
                )
                .foregroundStyle(
                    .linearGradient(
                        colors: [.blue.opacity(0.3), .blue.opacity(0.1)],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
                .interpolationMethod(.catmullRom)
            }
            .frame(height: 200)
            .chartXAxis {
                AxisMarks(values: .stride(by: timeframe == .week ? .day : .month)) { _ in
                    AxisGridLine()
                    AxisTick()
                    AxisValueLabel(format: .dateTime.month().day())
                }
            }
            .chartYAxis {
                AxisMarks { _ in
                    AxisGridLine()
                    AxisTick()
                    AxisValueLabel()
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(radius: 2)
        )
    }
}

struct SpeciesDistributionCard: View {
    let speciesData: [SpeciesDataPoint]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Species Contributions")
                .font(.headline)
                .fontWeight(.semibold)

            Chart(speciesData) { species in
                BarMark(
                    x: .value("Count", species.count),
                    y: .value("Species", species.name)
                )
                .foregroundStyle(by: .value("Species", species.name))
            }
            .frame(height: 200)
            .chartLegend(.hidden)
            .chartXAxis {
                AxisMarks { _ in
                    AxisGridLine()
                    AxisTick()
                    AxisValueLabel()
                }
            }
            .chartYAxis {
                AxisMarks { _ in
                    AxisTick()
                    AxisValueLabel()
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(radius: 2)
        )
    }
}

struct ResearchImpactCard: View {
    let impactData: ResearchImpactData

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Research Impact")
                .font(.headline)
                .fontWeight(.semibold)

            VStack(spacing: 12) {
                ImpactMetric(
                    title: "h-index",
                    value: "\(impactData.hIndex)",
                    description: "Research output and citations",
                    color: .blue
                )

                ImpactMetric(
                    title: "Collaboration Score",
                    value: "\(impactData.collaborationScore)",
                    description: "Cross-institutional partnerships",
                    color: .green
                )

                ImpactMetric(
                    title: "Data Quality Rating",
                    value: String(format: "%.1f", impactData.qualityRating),
                    description: "Peer-reviewed assessment",
                    color: .orange
                )

                ImpactMetric(
                    title: "Global Ranking",
                    value: "#\(impactData.globalRanking)",
                    description: "Among all researchers",
                    color: .purple
                )
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(radius: 2)
        )
    }
}

struct ImpactMetric: View {
    let title: String
    let value: String
    let description: String
    let color: Color

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)

                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Text(value)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(color)
        }
        .padding(.vertical, 4)
    }
}

struct StatItem: View {
    let title: String
    let value: String
    let icon: String

    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.blue)

            Text(value)
                .font(.headline)
                .fontWeight(.bold)

            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
    }
}
```

---

## Shared Infrastructure and Services

### Network Service (`NetworkService.swift`)

```swift
import Foundation
import Combine

class NetworkService: ObservableObject {
    static let shared = NetworkService()

    private let baseURL = "https://api.sharktrack.org"
    private let session = URLSession.shared
    private var cancellables = Set<AnyCancellable>()

    @Published var isOnline = true
    @Published var uploadQueue: [PendingUpload] = []

    private init() {
        setupNetworkMonitoring()
        loadUploadQueue()
    }

    // MARK: - Authentication

    func authenticate(email: String, password: String) -> AnyPublisher<AuthResponse, Error> {
        let endpoint = "\(baseURL)/auth/login"
        let body = ["email": email, "password": password]

        return makeRequest(endpoint: endpoint, method: "POST", body: body)
    }

    func refreshToken() -> AnyPublisher<AuthResponse, Error> {
        let endpoint = "\(baseURL)/auth/refresh"
        return makeRequest(endpoint: endpoint, method: "POST")
    }

    // MARK: - Video Upload

    func uploadVideo(
        videoURL: URL,
        metadata: VideoMetadata,
        progressHandler: @escaping (Double) -> Void
    ) -> AnyPublisher<UploadResponse, Error> {

        let endpoint = "\(baseURL)/api/upload/mobile"

        return Future { promise in
            var request = URLRequest(url: URL(string: endpoint)!)
            request.httpMethod = "POST"

            let boundary = UUID().uuidString
            request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

            // Add authorization header
            if let token = AuthenticationManager.shared.currentToken {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }

            var body = Data()

            // Add metadata
            if let metadataData = try? JSONEncoder().encode(metadata) {
                body.append("--\(boundary)\r\n".data(using: .utf8)!)
                body.append("Content-Disposition: form-data; name=\"metadata\"\r\n\r\n".data(using: .utf8)!)
                body.append(metadataData)
                body.append("\r\n".data(using: .utf8)!)
            }

            // Add video file
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"video\"; filename=\"\(videoURL.lastPathComponent)\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: video/mp4\r\n\r\n".data(using: .utf8)!)

            do {
                let videoData = try Data(contentsOf: videoURL)
                body.append(videoData)
            } catch {
                promise(.failure(error))
                return
            }

            body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

            let task = self.session.uploadTask(with: request, from: body) { data, response, error in
                if let error = error {
                    promise(.failure(error))
                    return
                }

                guard let data = data else {
                    promise(.failure(NetworkError.noData))
                    return
                }

                do {
                    let uploadResponse = try JSONDecoder().decode(UploadResponse.self, from: data)
                    promise(.success(uploadResponse))
                } catch {
                    promise(.failure(error))
                }
            }

            // Track upload progress
            let observation = task.progress.observe(\.fractionCompleted) { progress, _ in
                DispatchQueue.main.async {
                    progressHandler(progress.fractionCompleted)
                }
            }

            task.resume()
        }
        .eraseToAnyPublisher()
    }

    // MARK: - Analytics

    func getPersonalAnalytics(timeframe: String) -> AnyPublisher<PersonalStats, Error> {
        let endpoint = "\(baseURL)/api/analytics/personal?timeframe=\(timeframe)"
        return makeRequest(endpoint: endpoint, method: "GET")
    }

    func getGlobalNetworkStatus() -> AnyPublisher<NetworkData, Error> {
        let endpoint = "\(baseURL)/api/network/status"
        return makeRequest(endpoint: endpoint, method: "GET")
    }

    // MARK: - Species Data

    func getSpeciesIntelligence(speciesId: String) -> AnyPublisher<SpeciesIntelligence, Error> {
        let endpoint = "\(baseURL)/api/species/\(speciesId)"
        return makeRequest(endpoint: endpoint, method: "GET")
    }

    func searchSpecies(query: String) -> AnyPublisher<[SpeciesSearchResult], Error> {
        let endpoint = "\(baseURL)/api/species/search?q=\(query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")"
        return makeRequest(endpoint: endpoint, method: "GET")
    }

    // MARK: - Offline Support

    func queueUpload(_ upload: PendingUpload) {
        uploadQueue.append(upload)
        saveUploadQueue()

        if isOnline {
            processUploadQueue()
        }
    }

    private func processUploadQueue() {
        guard isOnline else { return }

        for upload in uploadQueue {
            uploadVideo(
                videoURL: upload.videoURL,
                metadata: upload.metadata,
                progressHandler: { _ in }
            )
            .sink(
                receiveCompletion: { completion in
                    if case .finished = completion {
                        self.removeFromUploadQueue(upload)
                    }
                },
                receiveValue: { _ in }
            )
            .store(in: &cancellables)
        }
    }

    private func removeFromUploadQueue(_ upload: PendingUpload) {
        uploadQueue.removeAll { $0.id == upload.id }
        saveUploadQueue()
    }

    // MARK: - Private Methods

    private func makeRequest<T: Codable>(
        endpoint: String,
        method: String,
        body: [String: Any]? = nil
    ) -> AnyPublisher<T, Error> {

        guard let url = URL(string: endpoint) else {
            return Fail(error: NetworkError.invalidURL)
                .eraseToAnyPublisher()
        }

        var request = URLRequest(url: url)
        request.httpMethod = method

        // Add authorization header
        if let token = AuthenticationManager.shared.currentToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        // Add body for POST requests
        if let body = body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            do {
                request.httpBody = try JSONSerialization.data(withJSONObject: body)
            } catch {
                return Fail(error: error)
                    .eraseToAnyPublisher()
            }
        }

        return session.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: T.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    private func setupNetworkMonitoring() {
        // Network reachability monitoring would go here
        // Using Network framework or third-party solution
    }

    private func loadUploadQueue() {
        // Load pending uploads from UserDefaults or Core Data
    }

    private func saveUploadQueue() {
        // Save pending uploads to persistent storage
    }
}

enum NetworkError: Error {
    case invalidURL
    case noData
    case unauthorized
    case serverError(Int)
}
```

### Local Database (`CoreDataManager.swift`)

```swift
import CoreData
import Foundation

class CoreDataManager: ObservableObject {
    static let shared = CoreDataManager()

    lazy var persistentContainer: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "SharkTrackModel")
        container.loadPersistentStores { _, error in
            if let error = error {
                fatalError("Core Data error: \(error)")
            }
        }
        return container
    }()

    var viewContext: NSManagedObjectContext {
        return persistentContainer.viewContext
    }

    private init() {}

    func save() {
        if viewContext.hasChanges {
            do {
                try viewContext.save()
            } catch {
                print("Failed to save context: \(error)")
            }
        }
    }

    // MARK: - Video Management

    func saveVideo(url: URL, metadata: VideoMetadata) -> LocalVideo {
        let video = LocalVideo(context: viewContext)
        video.id = UUID()
        video.localURL = url
        video.title = metadata.title
        video.recordedAt = Date()
        video.uploadStatus = "pending"
        video.metadata = try? JSONEncoder().encode(metadata)

        save()
        return video
    }

    func getPendingUploads() -> [LocalVideo] {
        let request: NSFetchRequest<LocalVideo> = LocalVideo.fetchRequest()
        request.predicate = NSPredicate(format: "uploadStatus == %@", "pending")

        do {
            return try viewContext.fetch(request)
        } catch {
            print("Failed to fetch pending uploads: \(error)")
            return []
        }
    }

    func updateUploadStatus(video: LocalVideo, status: String) {
        video.uploadStatus = status
        save()
    }

    // MARK: - Analytics Cache

    func cacheAnalyticsData(_ data: PersonalStats) {
        let analytics = CachedAnalytics(context: viewContext)
        analytics.id = UUID()
        analytics.cachedAt = Date()
        analytics.data = try? JSONEncoder().encode(data)

        save()
    }

    func getCachedAnalytics() -> PersonalStats? {
        let request: NSFetchRequest<CachedAnalytics> = CachedAnalytics.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(key: "cachedAt", ascending: false)]
        request.fetchLimit = 1

        do {
            if let cached = try viewContext.fetch(request).first,
               let data = cached.data {
                return try JSONDecoder().decode(PersonalStats.self, from: data)
            }
        } catch {
            print("Failed to load cached analytics: \(error)")
        }

        return nil
    }
}
```

---

## Cross-Platform Integration and Deployment

### Flutter Alternative (Shared Codebase)

For organizations preferring a single codebase, here's a Flutter implementation outline:

```dart
// main.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:camera/camera.dart';
import 'package:location/location.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize cameras
  final cameras = await availableCameras();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => LocationProvider()),
        ChangeNotifierProvider(create: (_) => UploadProvider()),
        ChangeNotifierProvider(create: (_) => AnalyticsProvider()),
      ],
      child: SharkTrackApp(cameras: cameras),
    ),
  );
}

class SharkTrackApp extends StatelessWidget {
  final List<CameraDescription> cameras;

  const SharkTrackApp({Key? key, required this.cameras}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SharkTrack Field',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: Consumer<AuthProvider>(
        builder: (context, auth, _) {
          if (auth.isAuthenticated) {
            return MainTabView(cameras: cameras);
          } else {
            return LoginScreen();
          }
        },
      ),
    );
  }
}

// Camera recording widget
class CameraRecordingWidget extends StatefulWidget {
  final List<CameraDescription> cameras;

  const CameraRecordingWidget({Key? key, required this.cameras}) : super(key: key);

  @override
  _CameraRecordingWidgetState createState() => _CameraRecordingWidgetState();
}

class _CameraRecordingWidgetState extends State<CameraRecordingWidget> {
  CameraController? _controller;
  bool _isRecording = false;
  Duration _recordingDuration = Duration.zero;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    final camera = widget.cameras.first;
    _controller = CameraController(
      camera,
      ResolutionPreset.high,
      enableAudio: true,
    );

    await _controller!.initialize();
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    if (_controller == null || !_controller!.value.isInitialized) {
      return Center(child: CircularProgressIndicator());
    }

    return Stack(
      children: [
        CameraPreview(_controller!),

        // Recording controls
        Positioned(
          bottom: 50,
          left: 0,
          right: 0,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // Flash toggle
              IconButton(
                onPressed: _toggleFlash,
                icon: Icon(
                  _controller!.value.flashMode == FlashMode.torch
                    ? Icons.flash_on
                    : Icons.flash_off,
                  color: Colors.white,
                  size: 30,
                ),
              ),

              // Record button
              GestureDetector(
                onTap: _isRecording ? _stopRecording : _startRecording,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white,
                  ),
                  child: Center(
                    child: Container(
                      width: 60,
                      height: 60,
                      decoration: BoxDecoration(
                        shape: _isRecording ? BoxShape.rectangle : BoxShape.circle,
                        color: Colors.red,
                        borderRadius: _isRecording ? BorderRadius.circular(8) : null,
                      ),
                    ),
                  ),
                ),
              ),

              // Camera switch
              IconButton(
                onPressed: _switchCamera,
                icon: Icon(
                  Icons.switch_camera,
                  color: Colors.white,
                  size: 30,
                ),
              ),
            ],
          ),
        ),

        // Recording status
        if (_isRecording)
          Positioned(
            top: 100,
            left: 20,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.7),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                    ),
                  ),
                  SizedBox(width: 8),
                  Text(
                    _formatDuration(_recordingDuration),
                    style: TextStyle(color: Colors.white),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }

  Future<void> _startRecording() async {
    try {
      await _controller!.startVideoRecording();
      setState(() {
        _isRecording = true;
      });

      _timer = Timer.periodic(Duration(seconds: 1), (timer) {
        setState(() {
          _recordingDuration = Duration(seconds: timer.tick);
        });
      });
    } catch (e) {
      print('Error starting recording: $e');
    }
  }

  Future<void> _stopRecording() async {
    try {
      final videoFile = await _controller!.stopVideoRecording();
      _timer?.cancel();

      setState(() {
        _isRecording = false;
        _recordingDuration = Duration.zero;
      });

      // Navigate to metadata form
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => VideoMetadataForm(videoPath: videoFile.path),
        ),
      );
    } catch (e) {
      print('Error stopping recording: $e');
    }
  }

  Future<void> _toggleFlash() async {
    final flashMode = _controller!.value.flashMode == FlashMode.torch
      ? FlashMode.off
      : FlashMode.torch;

    await _controller!.setFlashMode(flashMode);
    setState(() {});
  }

  Future<void> _switchCamera() async {
    final cameras = await availableCameras();
    final currentIndex = cameras.indexOf(_controller!.description);
    final nextIndex = (currentIndex + 1) % cameras.length;

    await _controller!.dispose();
    _controller = CameraController(
      cameras[nextIndex],
      ResolutionPreset.high,
      enableAudio: true,
    );

    await _controller!.initialize();
    setState(() {});
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, "0");
    String minutes = twoDigits(duration.inMinutes);
    String seconds = twoDigits(duration.inSeconds.remainder(60));
    return "$minutes:$seconds";
  }

  @override
  void dispose() {
    _timer?.cancel();
    _controller?.dispose();
    super.dispose();
  }
}
```

---

## Deployment and Distribution

### App Store Configuration

#### iOS App Store (`ios/Runner/Info.plist`)

```xml
<key>NSCameraUsageDescription</key>
<string>SharkTrack needs camera access to record marine research videos</string>
<key>NSMicrophoneUsageDescription</key>
<string>SharkTrack needs microphone access to record audio with videos</string>
<key>NSLocationWhenInUseUsageDescription</key>
<string>SharkTrack needs location access to add GPS coordinates to research videos</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>SharkTrack needs location access to add GPS coordinates to research videos</string>
```

#### Android Permissions (`android/app/src/main/AndroidManifest.xml`)

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<uses-feature android:name="android.hardware.camera" android:required="true" />
<uses-feature android:name="android.hardware.camera.autofocus" />
<uses-feature android:name="android.hardware.location" android:required="true" />
<uses-feature android:name="android.hardware.location.gps" />
```

### Build and Distribution Scripts

#### Fastlane Configuration (`fastlane/Fastfile`)

```ruby
default_platform(:ios)

platform :ios do
  desc "Build and upload to TestFlight"
  lane :beta do
    build_app(
      scheme: "SharkTrackField",
      export_method: "app-store"
    )
    upload_to_testflight(
      skip_waiting_for_build_processing: true
    )
  end

  desc "Build and upload to App Store"
  lane :release do
    build_app(
      scheme: "SharkTrackField",
      export_method: "app-store"
    )
    upload_to_app_store(
      force: true,
      submit_for_review: true
    )
  end
end

platform :android do
  desc "Build and upload to Play Console"
  lane :beta do
    gradle(
      task: "bundle",
      build_type: "release"
    )
    upload_to_play_store(
      track: "internal",
      aab: "app/build/outputs/bundle/release/app-release.aab"
    )
  end

  desc "Deploy to Play Store"
  lane :release do
    gradle(
      task: "bundle",
      build_type: "release"
    )
    upload_to_play_store(
      track: "production",
      aab: "app/build/outputs/bundle/release/app-release.aab"
    )
  end
end
```

This comprehensive mobile application suite provides field researchers with powerful tools for data collection, analysis, and collaboration, seamlessly integrating with the broader SharkTrack platform ecosystem.