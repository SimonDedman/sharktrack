"""
Enhanced Batch Processing System for Marine Video Analysis
Integrates metadata extraction, substrate classification, and multi-folder processing
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime
import pandas as pd

# Import our new modules
from .metadata_extractor import MetadataExtractor, VideoMetadata, GPSLocation, EnvironmentalContext
from .substrate_classifier import AdvancedSubstrateClassifier, SubstrateClassification
from .database_integration import DatabaseIntegrator, get_location_context


@dataclass
class ProcessingJob:
    """Individual video processing job"""
    video_path: str
    output_path: str
    metadata_template: Optional[str] = None
    user_substrate: Optional[str] = None
    priority: int = 1  # Higher = processed first
    status: str = "pending"  # pending, processing, completed, failed
    error_message: Optional[str] = None


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing"""
    input_directory: str
    output_directory: str
    metadata_template: Optional[str] = None
    substrate_model_path: Optional[str] = None
    species_classifier_path: Optional[str] = None
    max_workers: int = 4
    recursive_search: bool = True
    video_extensions: List[str] = None
    enable_substrate_classification: bool = True
    enable_database_lookup: bool = True
    enable_metadata_export: bool = True
    create_summary_report: bool = True


@dataclass
class ProcessingResults:
    """Results from batch processing"""
    total_videos: int
    successful: int
    failed: int
    processing_time: float
    job_results: List[Dict]
    summary_statistics: Dict
    output_directory: str


class EnhancedBatchProcessor:
    """Enhanced batch processor with integrated metadata and substrate analysis"""

    def __init__(self, config: BatchProcessingConfig):
        self.config = config
        self.jobs: List[ProcessingJob] = []
        self.results: List[Dict] = []
        self.lock = threading.Lock()

        # Initialize components
        self.metadata_extractor = MetadataExtractor()
        self.substrate_classifier = AdvancedSubstrateClassifier(config.substrate_model_path)
        self.database_integrator = DatabaseIntegrator()

        # Ensure output directory exists
        Path(config.output_directory).mkdir(parents=True, exist_ok=True)

        # Default video extensions
        if config.video_extensions is None:
            self.config.video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.MP4', '.AVI', '.MOV', '.MKV']

    def discover_videos(self) -> List[str]:
        """Discover all video files in input directory"""
        input_path = Path(self.config.input_directory)
        video_files = []

        if self.config.recursive_search:
            # Recursive search
            for ext in self.config.video_extensions:
                video_files.extend(input_path.rglob(f'*{ext}'))
        else:
            # Single directory search
            for ext in self.config.video_extensions:
                video_files.extend(input_path.glob(f'*{ext}'))

        return [str(f) for f in video_files]

    def create_jobs(self) -> int:
        """Create processing jobs from discovered videos"""
        video_files = self.discover_videos()

        print(f"Discovered {len(video_files)} video files")

        for video_path in video_files:
            video_path_obj = Path(video_path)

            # Create relative output path structure
            relative_path = video_path_obj.relative_to(self.config.input_directory)
            output_subdir = Path(self.config.output_directory) / relative_path.parent / f"{relative_path.stem}_analysis"

            # Look for metadata template
            metadata_template = None
            if self.config.metadata_template:
                template_path = video_path_obj.parent / self.config.metadata_template
                if template_path.exists():
                    metadata_template = str(template_path)

            # Look for user substrate input (from filename or metadata)
            user_substrate = self._extract_substrate_from_filename(video_path_obj.name)

            job = ProcessingJob(
                video_path=video_path,
                output_path=str(output_subdir),
                metadata_template=metadata_template,
                user_substrate=user_substrate
            )

            self.jobs.append(job)

        return len(self.jobs)

    def _extract_substrate_from_filename(self, filename: str) -> Optional[str]:
        """Extract substrate information from filename if encoded"""
        filename_lower = filename.lower()

        substrate_keywords = {
            'sand': ['sand', 'sandy'],
            'coral_reef': ['coral', 'reef'],
            'rock': ['rock', 'rocky', 'boulder'],
            'seagrass': ['seagrass', 'grass'],
            'kelp': ['kelp'],
            'rubble': ['rubble']
        }

        for substrate, keywords in substrate_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                return substrate

        return None

    def process_batch(self) -> ProcessingResults:
        """Process all jobs in the batch"""
        if not self.jobs:
            self.create_jobs()

        if not self.jobs:
            raise ValueError("No videos found to process")

        start_time = datetime.now()
        print(f"Starting batch processing of {len(self.jobs)} videos with {self.config.max_workers} workers")

        # Process jobs in parallel
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all jobs
            future_to_job = {
                executor.submit(self._process_single_video, job): job
                for job in self.jobs
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    result = future.result()
                    with self.lock:
                        self.results.append(result)
                        completed += 1

                    print(f"Completed {completed}/{len(self.jobs)}: {Path(job.video_path).name}")

                except Exception as e:
                    job.status = "failed"
                    job.error_message = str(e)
                    print(f"Failed {Path(job.video_path).name}: {e}")

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Calculate statistics
        successful = sum(1 for r in self.results if r['status'] == 'completed')
        failed = len(self.jobs) - successful

        # Create summary statistics
        summary_stats = self._generate_summary_statistics()

        # Create summary report if requested
        if self.config.create_summary_report:
            self._create_summary_report(summary_stats, processing_time)

        return ProcessingResults(
            total_videos=len(self.jobs),
            successful=successful,
            failed=failed,
            processing_time=processing_time,
            job_results=self.results,
            summary_statistics=summary_stats,
            output_directory=self.config.output_directory
        )

    def _process_single_video(self, job: ProcessingJob) -> Dict:
        """Process a single video with full metadata and substrate analysis"""
        job.status = "processing"

        try:
            video_path = Path(job.video_path)
            output_path = Path(job.output_path)
            output_path.mkdir(parents=True, exist_ok=True)

            # Extract comprehensive metadata
            print(f"Extracting metadata: {video_path.name}")
            metadata = self.metadata_extractor.extract_video_metadata(
                str(video_path),
                job.metadata_template
            )

            # Enhanced substrate classification
            substrate_result = None
            if self.config.enable_substrate_classification:
                print(f"Classifying substrate: {video_path.name}")
                substrate_result = self._classify_substrate_comprehensive(
                    video_path, metadata, job.user_substrate
                )

                # Update metadata with substrate classification
                if substrate_result and metadata.environment:
                    metadata.environment.substrate_type = substrate_result.substrate_type
                    metadata.environment.substrate_confidence = substrate_result.confidence

            # Database enrichment
            if self.config.enable_database_lookup and metadata.gps_location:
                print(f"Enriching with database: {video_path.name}")
                self._enrich_with_database_data(metadata)

            # Export metadata
            if self.config.enable_metadata_export:
                metadata_file = output_path / f"{video_path.stem}_metadata.json"
                self.metadata_extractor.export_metadata(metadata, str(metadata_file))

            # Prepare result
            result = {
                'video_path': str(video_path),
                'output_path': str(output_path),
                'status': 'completed',
                'metadata': asdict(metadata),
                'substrate_classification': asdict(substrate_result) if substrate_result else None,
                'processing_timestamp': datetime.now().isoformat()
            }

            job.status = "completed"
            return result

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)

            return {
                'video_path': job.video_path,
                'output_path': job.output_path,
                'status': 'failed',
                'error': str(e),
                'processing_timestamp': datetime.now().isoformat()
            }

    def _classify_substrate_comprehensive(self, video_path: Path, metadata: VideoMetadata,
                                        user_substrate: Optional[str]) -> Optional[SubstrateClassification]:
        """Comprehensive substrate classification using all available methods"""
        try:
            # Extract frames for analysis
            import cv2
            cap = cv2.VideoCapture(str(video_path))
            frames = []

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            # Sample frames throughout the video
            sample_indices = np.linspace(0, frame_count - 1, min(10, frame_count), dtype=int)

            for idx in sample_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)

            cap.release()

            if not frames:
                return None

            # Get GPS location and depth
            gps_location = None
            depth = None

            if metadata.gps_location:
                gps_location = (metadata.gps_location.latitude, metadata.gps_location.longitude)

            if metadata.environment and metadata.environment.depth_estimate:
                depth = metadata.environment.depth_estimate

            # Classify substrate using all methods
            substrate_result = self.substrate_classifier.classify_substrate(
                frames=frames,
                gps_location=gps_location,
                depth=depth,
                user_input=user_substrate
            )

            return substrate_result

        except Exception as e:
            print(f"Substrate classification failed for {video_path}: {e}")
            return None

    def _enrich_with_database_data(self, metadata: VideoMetadata):
        """Enrich metadata with external database information"""
        if not metadata.gps_location:
            return

        try:
            lat = metadata.gps_location.latitude
            lon = metadata.gps_location.longitude
            depth = metadata.environment.depth_estimate if metadata.environment else None

            # Get comprehensive location context
            context = get_location_context(lat, lon, depth)

            # Update environmental context with database information
            if not metadata.environment:
                metadata.environment = EnvironmentalContext()

            # Bathymetric data
            if context['bathymetric']:
                best_bathy = max(context['bathymetric'], key=lambda x: x.confidence or 0)
                if not metadata.environment.depth_estimate:
                    metadata.environment.depth_estimate = abs(best_bathy.depth)

                # Update substrate if not already classified with high confidence
                if (not metadata.environment.substrate_type or
                    (metadata.environment.substrate_confidence or 0) < 0.5):
                    metadata.environment.substrate_type = best_bathy.substrate_prediction
                    metadata.environment.substrate_confidence = best_bathy.confidence

            # Environmental data
            if context['environmental']:
                best_env = max(context['environmental'], key=lambda x: 1.0)  # All have equal weight
                if not metadata.environment.temperature:
                    metadata.environment.temperature = best_env.temperature

            # Add species distribution information to user metadata
            if context['species']:
                expected_species = [s.species_name for s in context['species'] if s.probability > 0.2]
                if not metadata.user_metadata:
                    metadata.user_metadata = {}
                metadata.user_metadata['expected_species'] = expected_species

        except Exception as e:
            print(f"Database enrichment failed: {e}")

    def _generate_summary_statistics(self) -> Dict:
        """Generate summary statistics from processing results"""
        stats = {
            'total_videos': len(self.results),
            'substrate_types': {},
            'geographic_distribution': {},
            'depth_distribution': [],
            'quality_metrics': {},
            'species_detections': {}
        }

        for result in self.results:
            if result['status'] != 'completed':
                continue

            metadata = result.get('metadata', {})
            environment = metadata.get('environment', {})
            gps_location = metadata.get('gps_location', {})

            # Substrate distribution
            substrate = environment.get('substrate_type')
            if substrate:
                stats['substrate_types'][substrate] = stats['substrate_types'].get(substrate, 0) + 1

            # Geographic distribution
            if gps_location:
                lat = gps_location.get('latitude')
                if lat:
                    if -30 <= lat <= 30:
                        region = 'tropical'
                    elif abs(lat) > 60:
                        region = 'polar'
                    else:
                        region = 'temperate'

                    stats['geographic_distribution'][region] = stats['geographic_distribution'].get(region, 0) + 1

            # Depth distribution
            depth = environment.get('depth_estimate')
            if depth:
                stats['depth_distribution'].append(depth)

            # Quality metrics
            clarity = environment.get('water_clarity')
            if clarity:
                if 'water_clarity' not in stats['quality_metrics']:
                    stats['quality_metrics']['water_clarity'] = []
                stats['quality_metrics']['water_clarity'].append(clarity)

        # Calculate depth statistics
        if stats['depth_distribution']:
            import numpy as np
            depths = np.array(stats['depth_distribution'])
            stats['depth_statistics'] = {
                'mean_depth': float(np.mean(depths)),
                'median_depth': float(np.median(depths)),
                'min_depth': float(np.min(depths)),
                'max_depth': float(np.max(depths))
            }

        return stats

    def _create_summary_report(self, stats: Dict, processing_time: float):
        """Create a comprehensive summary report"""
        report_path = Path(self.config.output_directory) / "batch_processing_summary.md"

        with open(report_path, 'w') as f:
            f.write(f"# Batch Processing Summary Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Processing Time:** {processing_time:.2f} seconds\n")
            f.write(f"**Total Videos:** {stats['total_videos']}\n\n")

            # Substrate distribution
            f.write("## Substrate Distribution\n\n")
            for substrate, count in stats['substrate_types'].items():
                f.write(f"- **{substrate.replace('_', ' ').title()}:** {count}\n")
            f.write("\n")

            # Geographic distribution
            f.write("## Geographic Distribution\n\n")
            for region, count in stats['geographic_distribution'].items():
                f.write(f"- **{region.title()}:** {count}\n")
            f.write("\n")

            # Depth statistics
            if 'depth_statistics' in stats:
                depth_stats = stats['depth_statistics']
                f.write("## Depth Analysis\n\n")
                f.write(f"- **Mean Depth:** {depth_stats['mean_depth']:.1f}m\n")
                f.write(f"- **Median Depth:** {depth_stats['median_depth']:.1f}m\n")
                f.write(f"- **Depth Range:** {depth_stats['min_depth']:.1f}m - {depth_stats['max_depth']:.1f}m\n\n")

            # Processing details
            f.write("## Processing Configuration\n\n")
            f.write(f"- **Input Directory:** {self.config.input_directory}\n")
            f.write(f"- **Output Directory:** {self.config.output_directory}\n")
            f.write(f"- **Max Workers:** {self.config.max_workers}\n")
            f.write(f"- **Substrate Classification:** {'Enabled' if self.config.enable_substrate_classification else 'Disabled'}\n")
            f.write(f"- **Database Lookup:** {'Enabled' if self.config.enable_database_lookup else 'Disabled'}\n")

        print(f"Summary report created: {report_path}")

        # Also create a CSV summary for data analysis
        self._create_csv_summary(stats)

    def _create_csv_summary(self, stats: Dict):
        """Create CSV summary of results"""
        csv_path = Path(self.config.output_directory) / "batch_results.csv"

        rows = []
        for result in self.results:
            if result['status'] != 'completed':
                continue

            metadata = result.get('metadata', {})
            environment = metadata.get('environment', {})
            gps_location = metadata.get('gps_location', {})

            row = {
                'video_path': result['video_path'],
                'substrate_type': environment.get('substrate_type'),
                'substrate_confidence': environment.get('substrate_confidence'),
                'latitude': gps_location.get('latitude') if gps_location else None,
                'longitude': gps_location.get('longitude') if gps_location else None,
                'depth': environment.get('depth_estimate'),
                'water_clarity': environment.get('water_clarity'),
                'light_level': environment.get('light_level'),
                'processing_timestamp': result['processing_timestamp']
            }

            rows.append(row)

        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(csv_path, index=False)
            print(f"CSV summary created: {csv_path}")


# Convenience functions
def process_video_directory(input_dir: str, output_dir: str, **kwargs) -> ProcessingResults:
    """Convenience function to process a directory of videos"""

    config = BatchProcessingConfig(
        input_directory=input_dir,
        output_directory=output_dir,
        **kwargs
    )

    processor = EnhancedBatchProcessor(config)
    return processor.process_batch()


def create_processing_config(input_dir: str, output_dir: str) -> BatchProcessingConfig:
    """Create a default processing configuration"""
    return BatchProcessingConfig(
        input_directory=input_dir,
        output_directory=output_dir,
        recursive_search=True,
        max_workers=4,
        enable_substrate_classification=True,
        enable_database_lookup=True,
        enable_metadata_export=True,
        create_summary_report=True
    )