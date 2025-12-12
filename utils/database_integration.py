"""
External Database Integration for Marine Video Analysis
Connects to bathymetric, species distribution, and environmental databases
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import numpy as np
from urllib.parse import urlencode
import time


@dataclass
class BathymetricData:
    """Bathymetric information for a location"""
    depth: float  # meters (negative = below sea level)
    slope: Optional[float] = None  # degrees
    aspect: Optional[float] = None  # degrees
    substrate_prediction: Optional[str] = None
    confidence: Optional[float] = None
    source: str = "unknown"


@dataclass
class SpeciesDistribution:
    """Species distribution information"""
    species_name: str
    probability: float  # 0-1
    seasonal_variation: Optional[Dict] = None
    depth_range: Optional[Tuple[float, float]] = None
    source: str = "unknown"


@dataclass
class EnvironmentalData:
    """Environmental data for a location"""
    temperature: Optional[float] = None  # Celsius
    salinity: Optional[float] = None  # PSU
    chlorophyll: Optional[float] = None  # mg/m³
    current_speed: Optional[float] = None  # m/s
    current_direction: Optional[float] = None  # degrees
    source: str = "unknown"


class DatabaseIntegrator:
    """Integrate with external marine databases"""

    def __init__(self, cache_dir: Optional[str] = None, enable_cache: bool = True):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".sharktrack_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.enable_cache = enable_cache

        # Initialize local cache database
        if enable_cache:
            self.cache_db = self.cache_dir / "database_cache.sqlite"
            self._init_cache_db()

        # API endpoints (these would need to be updated with real endpoints)
        self.endpoints = {
            'gebco': 'https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/',
            'noaa': 'https://www.ncei.noaa.gov/erddap/',
            'obis': 'https://api.obis.org/',
            'hycom': 'https://tds.hycom.org/thredds/',
            'reefbase': 'http://www.reefbase.org/api/',
            'fishbase': 'https://fishbase.se/webservice/',
        }

    def _init_cache_db(self):
        """Initialize SQLite cache database"""
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()

            # Bathymetric data cache
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bathymetric_cache (
                    lat REAL,
                    lon REAL,
                    depth REAL,
                    slope REAL,
                    substrate_prediction TEXT,
                    confidence REAL,
                    source TEXT,
                    timestamp INTEGER,
                    PRIMARY KEY (lat, lon, source)
                )
            ''')

            # Species distribution cache
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS species_cache (
                    lat REAL,
                    lon REAL,
                    species_name TEXT,
                    probability REAL,
                    depth_min REAL,
                    depth_max REAL,
                    source TEXT,
                    timestamp INTEGER,
                    PRIMARY KEY (lat, lon, species_name, source)
                )
            ''')

            # Environmental data cache
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS environmental_cache (
                    lat REAL,
                    lon REAL,
                    temperature REAL,
                    salinity REAL,
                    chlorophyll REAL,
                    current_speed REAL,
                    current_direction REAL,
                    source TEXT,
                    timestamp INTEGER,
                    PRIMARY KEY (lat, lon, source)
                )
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Warning: Failed to initialize cache database: {e}")

    def get_bathymetric_data(self, lat: float, lon: float,
                           sources: List[str] = None) -> List[BathymetricData]:
        """Get bathymetric data for a location"""
        if sources is None:
            sources = ['gebco', 'noaa']

        results = []

        for source in sources:
            # Check cache first
            if self.enable_cache:
                cached_data = self._get_cached_bathymetric(lat, lon, source)
                if cached_data:
                    results.append(cached_data)
                    continue

            # Query external database
            try:
                data = self._query_bathymetric_database(lat, lon, source)
                if data:
                    results.append(data)

                    # Cache the result
                    if self.enable_cache:
                        self._cache_bathymetric_data(lat, lon, data)

            except Exception as e:
                print(f"Warning: Failed to query {source} for bathymetric data: {e}")
                continue

        return results

    def get_species_distribution(self, lat: float, lon: float, depth: Optional[float] = None,
                               sources: List[str] = None) -> List[SpeciesDistribution]:
        """Get species distribution data for a location"""
        if sources is None:
            sources = ['obis', 'fishbase']

        results = []

        for source in sources:
            # Check cache first
            if self.enable_cache:
                cached_data = self._get_cached_species(lat, lon, source)
                if cached_data:
                    results.extend(cached_data)
                    continue

            # Query external database
            try:
                data = self._query_species_database(lat, lon, depth, source)
                if data:
                    results.extend(data)

                    # Cache the results
                    if self.enable_cache:
                        for species_data in data:
                            self._cache_species_data(lat, lon, species_data)

            except Exception as e:
                print(f"Warning: Failed to query {source} for species data: {e}")
                continue

        return results

    def get_environmental_data(self, lat: float, lon: float,
                             sources: List[str] = None) -> List[EnvironmentalData]:
        """Get environmental data for a location"""
        if sources is None:
            sources = ['hycom', 'noaa']

        results = []

        for source in sources:
            # Check cache first
            if self.enable_cache:
                cached_data = self._get_cached_environmental(lat, lon, source)
                if cached_data:
                    results.append(cached_data)
                    continue

            # Query external database
            try:
                data = self._query_environmental_database(lat, lon, source)
                if data:
                    results.append(data)

                    # Cache the result
                    if self.enable_cache:
                        self._cache_environmental_data(lat, lon, data)

            except Exception as e:
                print(f"Warning: Failed to query {source} for environmental data: {e}")
                continue

        return results

    def _query_bathymetric_database(self, lat: float, lon: float, source: str) -> Optional[BathymetricData]:
        """Query bathymetric database (placeholder implementation)"""
        if source == 'gebco':
            return self._query_gebco(lat, lon)
        elif source == 'noaa':
            return self._query_noaa_bathymetry(lat, lon)
        else:
            # Fallback: simple depth estimation based on distance from shore
            return self._estimate_depth_simple(lat, lon)

    def _query_gebco(self, lat: float, lon: float) -> Optional[BathymetricData]:
        """Query GEBCO bathymetric database"""
        # This is a placeholder - real implementation would use GEBCO WMS/WCS services
        try:
            # Simulate database query with realistic depth estimation
            # Based on rough global patterns

            # Simple model: deeper water further from typical coastlines
            depth_estimate = self._estimate_depth_simple(lat, lon)

            if depth_estimate:
                return BathymetricData(
                    depth=depth_estimate.depth,
                    substrate_prediction=self._predict_substrate_from_depth(depth_estimate.depth, lat),
                    confidence=0.6,
                    source='gebco_simulated'
                )

        except Exception as e:
            print(f"GEBCO query failed: {e}")

        return None

    def _query_noaa_bathymetry(self, lat: float, lon: float) -> Optional[BathymetricData]:
        """Query NOAA bathymetric data"""
        # Placeholder implementation
        return None

    def _estimate_depth_simple(self, lat: float, lon: float) -> Optional[BathymetricData]:
        """Simple depth estimation based on geographic patterns"""
        # Very basic estimation - in reality would use proper bathymetric data

        # Check if coordinates are over land (very rough approximation)
        if self._is_likely_land(lat, lon):
            return None

        # Estimate depth based on rough oceanic patterns
        # This is very simplified and not accurate!

        # Distance from equator (affects ocean depth patterns)
        lat_factor = abs(lat) / 90.0

        # Longitude patterns (very rough continental shelf approximation)
        lon_factor = (abs(lon) % 40) / 40.0

        # Simple depth model
        estimated_depth = -(10 + lat_factor * 3000 + lon_factor * 500)

        # Add some randomness to avoid identical predictions
        estimated_depth += np.random.normal(0, 100)

        substrate = self._predict_substrate_from_depth(estimated_depth, lat)

        return BathymetricData(
            depth=estimated_depth,
            substrate_prediction=substrate,
            confidence=0.3,
            source='simple_estimation'
        )

    def _is_likely_land(self, lat: float, lon: float) -> bool:
        """Very rough check if coordinates are likely over land"""
        # This is extremely simplified - real implementation would use proper land masks

        # Some very rough continental approximations
        land_regions = [
            # North America
            (25, 50, -125, -60),
            # Europe
            (35, 70, -10, 40),
            # Africa
            (-35, 35, -20, 50),
            # Asia
            (0, 70, 40, 140),
            # Australia
            (-45, -10, 110, 155),
            # South America
            (-55, 15, -85, -35),
        ]

        for lat_min, lat_max, lon_min, lon_max in land_regions:
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return True

        return False

    def _predict_substrate_from_depth(self, depth: float, lat: float) -> str:
        """Predict substrate type from depth and latitude"""
        depth = abs(depth)  # Work with positive depth values

        # Very simplified substrate prediction
        if depth < 5:
            return "sand"  # Shallow areas often sandy
        elif depth < 30:
            if -30 <= lat <= 30:  # Tropical
                return "coral_reef"
            else:
                return "seagrass"
        elif depth < 100:
            return "sand"
        elif depth < 500:
            return "rock"
        else:
            return "unknown"

    def _query_species_database(self, lat: float, lon: float, depth: Optional[float],
                               source: str) -> List[SpeciesDistribution]:
        """Query species distribution database"""
        # Placeholder implementation with some realistic examples
        results = []

        # Simple geographic species distribution model
        if -30 <= lat <= 30:  # Tropical
            tropical_species = [
                ('Carcharhinus melanopterus', 0.3),  # Blacktip reef shark
                ('Stegostoma fasciatum', 0.2),        # Zebra shark
                ('Rhincodon typus', 0.1),             # Whale shark
            ]
            for species, prob in tropical_species:
                results.append(SpeciesDistribution(
                    species_name=species,
                    probability=prob,
                    depth_range=(0, 50),
                    source=f'{source}_simulated'
                ))

        elif abs(lat) > 50:  # Polar/subpolar
            cold_species = [
                ('Somniosus microcephalus', 0.4),     # Greenland shark
                ('Hexanchus griseus', 0.2),           # Bluntnose sixgill
            ]
            for species, prob in cold_species:
                results.append(SpeciesDistribution(
                    species_name=species,
                    probability=prob,
                    depth_range=(50, 500),
                    source=f'{source}_simulated'
                ))

        else:  # Temperate
            temperate_species = [
                ('Carcharodon carcharias', 0.3),      # Great white shark
                ('Triakis semifasciata', 0.4),        # Leopard shark
            ]
            for species, prob in temperate_species:
                results.append(SpeciesDistribution(
                    species_name=species,
                    probability=prob,
                    depth_range=(0, 200),
                    source=f'{source}_simulated'
                ))

        return results

    def _query_environmental_database(self, lat: float, lon: float, source: str) -> Optional[EnvironmentalData]:
        """Query environmental database"""
        # Placeholder implementation with realistic estimates

        # Simple temperature model based on latitude
        if abs(lat) < 30:  # Tropical
            temp = 25 + np.random.normal(0, 3)
        elif abs(lat) < 60:  # Temperate
            temp = 15 + np.random.normal(0, 5)
        else:  # Polar
            temp = 5 + np.random.normal(0, 3)

        # Simple salinity model
        salinity = 35 + np.random.normal(0, 2)

        return EnvironmentalData(
            temperature=temp,
            salinity=salinity,
            chlorophyll=np.random.uniform(0.1, 2.0),
            source=f'{source}_simulated'
        )

    # Cache management methods
    def _get_cached_bathymetric(self, lat: float, lon: float, source: str) -> Optional[BathymetricData]:
        """Get cached bathymetric data"""
        if not self.enable_cache:
            return None

        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()

            # Check for recent data (within 30 days)
            current_time = int(time.time())
            month_ago = current_time - (30 * 24 * 3600)

            cursor.execute('''
                SELECT depth, slope, substrate_prediction, confidence
                FROM bathymetric_cache
                WHERE abs(lat - ?) < 0.01 AND abs(lon - ?) < 0.01
                AND source = ? AND timestamp > ?
            ''', (lat, lon, source, month_ago))

            result = cursor.fetchone()
            conn.close()

            if result:
                return BathymetricData(
                    depth=result[0],
                    slope=result[1],
                    substrate_prediction=result[2],
                    confidence=result[3],
                    source=source
                )

        except Exception as e:
            print(f"Cache lookup failed: {e}")

        return None

    def _cache_bathymetric_data(self, lat: float, lon: float, data: BathymetricData):
        """Cache bathymetric data"""
        if not self.enable_cache:
            return

        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO bathymetric_cache
                (lat, lon, depth, slope, substrate_prediction, confidence, source, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (lat, lon, data.depth, data.slope, data.substrate_prediction,
                  data.confidence, data.source, int(time.time())))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Cache write failed: {e}")

    def _get_cached_species(self, lat: float, lon: float, source: str) -> List[SpeciesDistribution]:
        """Get cached species data"""
        # Similar implementation to bathymetric cache
        return []

    def _cache_species_data(self, lat: float, lon: float, data: SpeciesDistribution):
        """Cache species data"""
        # Similar implementation to bathymetric cache
        pass

    def _get_cached_environmental(self, lat: float, lon: float, source: str) -> Optional[EnvironmentalData]:
        """Get cached environmental data"""
        # Similar implementation to bathymetric cache
        return None

    def _cache_environmental_data(self, lat: float, lon: float, data: EnvironmentalData):
        """Cache environmental data"""
        # Similar implementation to bathymetric cache
        pass

    def clear_cache(self, older_than_days: int = 30):
        """Clear old cache entries"""
        if not self.enable_cache:
            return

        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()

            cutoff_time = int(time.time()) - (older_than_days * 24 * 3600)

            cursor.execute('DELETE FROM bathymetric_cache WHERE timestamp < ?', (cutoff_time,))
            cursor.execute('DELETE FROM species_cache WHERE timestamp < ?', (cutoff_time,))
            cursor.execute('DELETE FROM environmental_cache WHERE timestamp < ?', (cutoff_time,))

            conn.commit()
            conn.close()

            print(f"Cleared cache entries older than {older_than_days} days")

        except Exception as e:
            print(f"Cache cleanup failed: {e}")


# Convenience functions
def get_location_context(lat: float, lon: float, depth: Optional[float] = None) -> Dict:
    """Get comprehensive location context from all available databases"""
    integrator = DatabaseIntegrator()

    context = {
        'bathymetric': integrator.get_bathymetric_data(lat, lon),
        'species': integrator.get_species_distribution(lat, lon, depth),
        'environmental': integrator.get_environmental_data(lat, lon)
    }

    return context


def predict_substrate_from_location(lat: float, lon: float) -> Optional[str]:
    """Get substrate prediction from database lookup"""
    integrator = DatabaseIntegrator()
    bathymetric_data = integrator.get_bathymetric_data(lat, lon)

    if bathymetric_data:
        # Return substrate prediction from most confident source
        best_prediction = max(bathymetric_data, key=lambda x: x.confidence or 0)
        return best_prediction.substrate_prediction

    return None


def get_expected_species(lat: float, lon: float, depth: Optional[float] = None) -> List[str]:
    """Get list of species expected at a location"""
    integrator = DatabaseIntegrator()
    species_data = integrator.get_species_distribution(lat, lon, depth)

    # Return species with probability > 0.2
    expected_species = [s.species_name for s in species_data if s.probability > 0.2]
    return expected_species