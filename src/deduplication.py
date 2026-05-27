"""Deduplication logic - compares current scrape against history."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select

from src.database import HistoryDB, DbScrapeEvent
from src.models.vehicle import Vehicle

logger = logging.getLogger(__name__)


class VehicleDeduplicator:
    """Compares vehicles against history to detect new/unchanged/disappeared."""

    def __init__(self, db: HistoryDB):
        self.db = db

    def compare(self, vehicles: list[Vehicle]) -> dict[str, str]:
        """Compare current vehicles against database history.
        
        Returns a dict mapping vehicle_id -> status:
        - "new": vehicle not seen before
        - "unchanged": vehicle already seen with same ID
        - "disappeared": vehicle was seen before but not in current scrape
        """
        # Build status map for current vehicles
        status_map: dict[str, str] = {}
        seen_ids: set[str] = set()

        for v in vehicles:
            last = self.db.get_last_seen_vehicle(v.id)
            if last is None:
                status_map[v.id] = "new"
            else:
                status_map[v.id] = "unchanged"
            seen_ids.add(v.id)

        # Find disappeared vehicles
        # Get all vehicles that were in any previous scrape
        all_history = self.db.get_history(limit=10000)
        seen_before_ids = {r.id for r in all_history if r.id not in seen_ids and r.status in ("new", "unchanged")}

        # Mark disappeared vehicles
        for v_id in seen_before_ids:
            status_map[v_id] = "disappeared"

        # Log summary
        new_count = sum(1 for s in status_map.values() if s == "new")
        unchanged_count = sum(1 for s in status_map.values() if s == "unchanged")
        disappeared_count = sum(1 for s in status_map.values() if s == "disappeared")

        logger.info(
            "Dedup: %d new, %d unchanged, %d disappeared (of %d total)",
            new_count, unchanged_count, disappeared_count, len(status_map),
        )

        return status_map

    def get_new_vehicles(self, vehicles: list[Vehicle]) -> list[Vehicle]:
        """Get only vehicles that are new (never seen before)."""
        return [v for v in vehicles if self.db.get_last_seen_vehicle(v.id) is None]

    def get_disappeared(self) -> list[Vehicle]:
        """Get vehicles that disappeared from the latest scrape."""
        with self.db.session() as session:
            result = session.execute(
                select(DbScrapeEvent.scrape_id)
                .order_by(DbScrapeEvent.scrape_id.desc())
                .limit(1)
            )
            last_scrape_id = result.scalar()
        if not last_scrape_id:
            return []
        records = self.db.get_disappeared_vehicles(last_scrape_id=last_scrape_id)
        # Convert to Vehicle objects for consistency
        vehicles = []
        for r in records:
            vehicles.append(Vehicle(
                id=r.id,
                subasta=r.subasta,
                finSubasta=r.fin_subasta,
                codProvincia=r.cod_provincia,
                valoracion=r.valoracion,
                cargas=r.cargas,
                tipo=r.tipo,
                marcaModelo=r.marca_modelo,
                unicoPropietario=r.unico_propietario,
            ))
        return vehicles
