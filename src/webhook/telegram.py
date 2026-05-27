"""Telegram webhook module for vehicle auction notifications."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from src.models.vehicle import Vehicle

logger = logging.getLogger(__name__)


class TelegramWebhook:
    """Telegram webhook that sends notifications about vehicle auctions."""

    def __init__(
        self,
        token: str,
        chat_id: int,
        photos_dir: Optional[Path] = None,
    ):
        """Initialize Telegram webhook.
        
        Args:
            token: Telegram Bot API token
            chat_id: Telegram chat ID to send messages
            photos_dir: Directory to store downloaded photos
        """
        self.token = token  # Token completo: 8870806330:AAFVgtulPv1r2mbQN7paaBVwwSm-RLW37U8
        self.chat_id = chat_id
        self.photos_dir = photos_dir or Path(__file__).parent.parent / "photos"
        self.photos_dir.mkdir(parents=True, exist_ok=True)

    def _download_photo(
        self,
        photo_url: str,
        filename: str,
        vehicle_id: str,
        scrape_id: int,
    ) -> Optional[Path]:
        """Download and cache a photo.
        
        Args:
            photo_url: URL to the photo (AEAT serves relative paths)
            filename: Base filename
            vehicle_id: Unique vehicle ID
            scrape_id: Scrape session ID
            
        Returns:
            Path to downloaded photo or None on failure
        """
        try:
            import requests
            from pathlib import Path
            
            # Construct full URL for AEAT photos
            # AEAT serves photos at: https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/taiif/subastaInmuebles/data2/
            base_photo_url = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/taiif/subastaInmuebles/data2/"
            full_url = base_photo_url + photo_url
            
            # Create cache path
            cache_dir = self.photos_dir / vehicle_id
            cache_dir.mkdir(parents=True, exist_ok=True)
            photo_path = cache_dir / f"{filename}_{scrape_id}.jpg"
            
            # Download if not exists
            if not photo_path.exists():
                logger.info("Downloading photo: %s", photo_url)
                resp = requests.get(full_url, timeout=30)
                resp.raise_for_status()
                with open(photo_path, "wb") as f:
                    f.write(resp.content)
            
            return photo_path
            
        except Exception as e:
            logger.warning("Error downloading photo %s: %s", photo_url, e)
            return None

    def send_photo(
        self,
        photo_path: Path,
        caption: str,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Send a photo to Telegram.
        
        Args:
            photo_path: Path to photo file
            caption: Photo caption
            parse_mode: 'Markdown' or 'HTML'
            
        Returns:
            True on success
        """
        try:
            import requests
            
            # Prepare files
            with open(photo_path, "rb") as f:
                photo_file = (photo_path.name, f, "image/jpeg")
                files = {"photo": photo_file}
                
            # Prepare data
            data = {
                "chat_id": str(self.chat_id),
                "caption": caption,
                "parse_mode": parse_mode,
            }
            
            # Send
            resp = requests.post(
                "https://api.telegram.org/bot" + self.token,
                data=data,
                files=files,
                timeout=30,
            )
            resp.raise_for_status()
            return True
            
        except Exception as e:
            logger.warning("Error sending photo: %s", e)
            return False

    def send_text(
        self,
        message: str,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Send a text message to Telegram.
        
        Args:
            message: Message text
            parse_mode: 'Markdown' or 'HTML'
            
        Returns:
            True on success
        """
        try:
            import requests
            
            data = {
                "chat_id": str(self.chat_id),
                "text": message,
                "parse_mode": parse_mode,
            }
            
            resp = requests.post(
                "https://api.telegram.org/bot" + self.token,
                data=data,
                timeout=30,
            )
            resp.raise_for_status()
            return True
            
        except Exception as e:
            logger.warning("Error sending message: %s", e)
            return False

    def notify_vehicles(self, vehicles: list[Vehicle]) -> bool:
        """Send notification for a list of vehicles.
        
        Args:
            vehicles: List of Vehicle objects
            
        Returns:
            True if all notifications sent successfully
        """
        if not vehicles:
            logger.info("No vehicles to notify")
            return True
            
        success_count = 0
        total_count = len(vehicles)
        
        for vehicle in vehicles:
            # Build caption
            caption = (
                f"*🚗 {vehicle.marca_modelo}*\n\n"
                f"📊 *Valoración*: {vehicle.valoracion:,.2f}€\n"
                f"⚖️ *Cargas*: {vehicle.cargas:,.2f}€\n"
                f"💰 *Neto*: {vehicle.valor_neto:,.2f}€\n\n"
                f"📁 *Tipo*: {vehicle.tipo_descripcion}\n"
                f"🔢 *Matrícula*: {vehicle.matricula or 'Sin matrícula'}\n"
                f"📅 *Fin subasta*: {vehicle.fin_subasta}\n\n"
                f"📍 *Provincia*: {vehicle.cod_provincia}\n"
            )
            
            # Send text message (photos not available from AEAT)
            sent = self.send_text(caption)
            if sent:
                success_count += 1
                
                # Stop after first message (Telegram rate limits)
                break
        
        logger.info(
            "Telegram notification: %d/%d vehicles sent",
            success_count,
            total_count,
        )
        return success_count > 0
