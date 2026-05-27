"""Image writer - downloads and manages vehicle photos."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
import requests

from src.models.vehicle import Vehicle

logger = logging.getLogger(__name__)

# Base URL for vehicle photos from AEAT
AEAT_PHOTOS_BASE = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/taiif/subastaInmuebles/data2/fotos"


class ImageWriter:
    """Downloads and manages vehicle photos from AEAT."""

    def __init__(self, photos_dir: str = "photos", timeout: int = 30):
        self.photos_dir = Path(photos_dir)
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })

    def get_photo_url(self, vehicle_id: str, filename: str) -> str:
        """Construct the URL for a vehicle photo."""
        return f"{AEAT_PHOTOS_BASE}/{vehicle_id}/{filename}"

    def download_photo(self, vehicle_id: str, filename: str) -> Optional[Path]:
        """Download a single photo for a vehicle.
        
        Returns:
            Path to downloaded file or None if failed
        """
        url = self.get_photo_url(vehicle_id, filename)
        vehicle_dir = self.photos_dir / vehicle_id
        vehicle_dir.mkdir(parents=True, exist_ok=True)
        dest_path = vehicle_dir / filename

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            with open(dest_path, "wb") as f:
                f.write(response.content)
            
            logger.info("Downloaded %s -> %s", url, dest_path)
            return dest_path
        except Exception as e:
            logger.error("Failed to download %s: %s", url, e)
            return None

    def download_all_photos(self, vehicle: Vehicle) -> list[Path]:
        """Download all photos for a vehicle.
        
        Returns:
            List of paths to downloaded photos
        """
        downloaded = []
        for filename in vehicle.fotos:
            path = self.download_photo(vehicle.id, filename)
            if path:
                downloaded.append(path)
        
        if downloaded:
            logger.info("Downloaded %d photos for vehicle %s", len(downloaded), vehicle.id)
        return downloaded

    def get_photo_paths(self, vehicle_id: str) -> list[Path]:
        """Get all photo paths for a vehicle.
        
        Returns:
            List of Path objects for existing photos
        """
        vehicle_dir = self.photos_dir / vehicle_id
        if not vehicle_dir.exists():
            return []
        return list(vehicle_dir.glob("*"))

    def get_first_photo(self, vehicle_id: str) -> Optional[Path]:
        """Get the first photo for a vehicle.
        
        Returns:
            Path to first photo or None
        """
        photos = self.get_photo_paths(vehicle_id)
        return photos[0] if photos else None

    def cleanup_empty_dirs(self):
        """Remove empty directories."""
        for vehicle_dir in self.photos_dir.iterdir():
            if vehicle_dir.is_dir() and not any(vehicle_dir.iterdir()):
                vehicle_dir.rmdir()
                logger.debug("Removed empty directory: %s", vehicle_dir)
