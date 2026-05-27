"""AEAT scraper - fetches and parses vehicle auction data."""

from __future__ import annotations

import re
import logging
from typing import Optional
import requests

from src.models.vehicle import Vehicle

logger = logging.getLogger(__name__)

# URL del archivo JS con los datos de la AEAT (actualizado diariamente)
AEAT_JS_URL = (
    "https://www2.agenciatributaria.gob.es/"
    "static_files/common/internet/dep/taiif/subastaInmuebles/"
    "data2/bienes.js"
)

# Regex para extraer el array vehiculosSubasta
VEHICULOS_RE = re.compile(
    r"const\s+vehiculosSubasta\s*=\s*\[(.*?)\];\s*const\s+fechaBienesSubasta",
    re.DOTALL,
)


class AEATScraper:
    """Scraper for AEAT vehicle auctions."""

    def __init__(self, url: str = AEAT_JS_URL, timeout: int = 30):
        self.url = url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })

    def fetch_raw(self) -> str:
        """Download the bienes.js file and return raw text.
        
        Raises:
            requests.RequestException: On network errors.
            ValueError: If the response doesn't contain expected data.
        """
        logger.info("Fetching AEAT data from %s", self.url)
        resp = self.session.get(self.url, timeout=self.timeout)
        resp.raise_for_status()

        if "vehiculosSubasta" not in resp.text:
            raise ValueError(
                "El archivo JS no contiene el array vehiculosSubasta. "
                "La estructura de la AEAT puede haber cambiado."
            )

        return resp.text

    def extract_vehicles_raw(self, raw: str) -> list[dict]:
        """Extract the vehiculosSubasta array from raw JS text.
        
        Uses a simple regex to find the JSON array. This works because
        the AEAT exports standard JSON inside the JS file.
        """
        match = VEHICULOS_RE.search(raw)
        if not match:
            raise ValueError("No se encontró el array vehiculosSubasta en el JS")

        json_str = match.group(1)
        import json

        return json.loads(json_str)

    def parse_vehicle(self, raw: dict) -> Vehicle:
        """Parse a raw vehicle dict into a Vehicle model."""
        # Map JS field names to pydantic aliases
        return Vehicle(**raw)

    def scrape(self) -> list[Vehicle]:
        """Full scrape pipeline: fetch → parse → return vehicles.
        
        Returns:
            List of Vehicle objects.
        """
        raw_text = self.fetch_raw()
        raw_vehicles = self.extract_vehicles_raw(raw_text)
        vehicles = [self.parse_vehicle(v) for v in raw_vehicles]
        logger.info("Scraped %d vehicles", len(vehicles))
        return vehicles

    def scrape_provinces(self) -> list[dict]:
        """Extract province counts from the inmuebles data.
        
        Returns a list of province info dicts with codProvincia and count.
        """
        raw_text = self.fetch_raw()
        import json

        # Also extract inmueblesSubasta for province info
        inmuebles_re = re.compile(
            r"const\s+inmueblesSubasta\s*=\s*\[(.*?)\];\s*const\s+mueblesSubasta",
            re.DOTALL,
        )
        match = inmuebles_re.search(raw_text)
        if not match:
            return []

        inmuebles = json.loads(match.group(1))
        province_counts: dict[int, int] = {}
        for i in inmuebles:
            cp = i.get("codProvincia")
            if cp:
                province_counts[cp] = province_counts.get(cp, 0) + 1

        return [
            {"codProvincia": k, "count": v}
            for k, v in sorted(province_counts.items())
        ]
