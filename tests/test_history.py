"""Tests for history and deduplication."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from src.database import HistoryDB
from src.deduplication import VehicleDeduplicator
from src.models.vehicle import Vehicle


SAMPLE_VEHICLE_1 = {
    "id": "V001",
    "subasta": "SUB-001",
    "finSubasta": "2026-06-08",
    "codProvincia": 28,
    "valoracion": 10000.0,
    "cargas": 0,
    "tipo": 101,
    "marcaModelo": "BMW 320D",
    "matricula": "1234ABC",
    "bastidor": "WF0XXXTT123456789",
    "plazas": 5,
    "combustible": "D",
    "cilindrada": 1995,
    "años": 3.5,
    "unicoPropietario": 1,
    "uso": 1,
    "fotos": ["001.jpg"],
}

SAMPLE_VEHICLE_2 = {
    "id": "V002",
    "subasta": "SUB-002",
    "finSubasta": "2026-06-15",
    "codProvincia": 4,
    "valoracion": 8000.0,
    "cargas": 0,
    "tipo": 103,
    "marcaModelo": "Ford Transit",
    "matricula": "5678DEF",
    "bastidor": "WF0XXXTT987654321",
    "plazas": 3,
    "combustible": "D",
    "cilindrada": 1997,
    "años": 5.2,
    "unicoPropietario": 0,
    "uso": 9,
    "fotos": ["001.jpg", "002.jpg"],
}


class TestHistoryDB:
    """Tests for the HistoryDB database layer."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create a test database."""
        db_path = str(tmp_path / "test_history.db")
        return HistoryDB(db_path=db_path)

    def test_create_database(self, db):
        """Database should be created on init."""
        assert db.db_path.exists()

    def test_record_scrape(self, db):
        """Scrape should be recorded with all vehicles."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        v2 = Vehicle(**SAMPLE_VEHICLE_2)
        vehicles = [v1, v2]
        status_map = {"V001": "new", "V002": "new"}
        
        event = db.record_scrape(vehicles, status_map)
        
        assert event.total_vehicles == 2
        assert event.new_vehicles == 2
        assert event.unchanged_vehicles == 0
        assert event.disappeared_vehicles == 0

    def test_scrape_id_increment(self, db):
        """Each scrape should get a unique ID."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        vehicles = [v1]
        
        db.record_scrape(vehicles, {"V001": "new"})
        db.record_scrape(vehicles, {"V001": "unchanged"})
        
        stats = db.get_stats()
        assert stats["total_scrapes"] == 2

    def test_get_last_seen(self, db):
        """Should return the last seen version of a vehicle."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        db.record_scrape([v1], {"V001": "new"})
        
        record = db.get_last_seen_vehicle("V001")
        assert record is not None
        assert record.id == "V001"
        assert record.status == "new"

    def test_get_last_seen_not_found(self, db):
        """Should return None for unknown vehicle."""
        record = db.get_last_seen_vehicle("UNKNOWN")
        assert record is None

    def test_get_disappeared(self, db):
        """Should return disappeared vehicles."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        db.record_scrape([v1], {"V001": "new"})  # scrape_id=1
        
        # Simulate second scrape where V001 is marked as disappeared
        v1_disappeared = Vehicle(**SAMPLE_VEHICLE_1)
        v1_disappeared.id = "V001"
        db.record_scrape([v1_disappeared], {"V001": "disappeared"})  # scrape_id=2
        
        disappeared = db.get_disappeared_vehicles(last_scrape_id=2)
        assert len(disappeared) >= 1

    def test_mark_seen(self, db):
        """Should mark vehicle as seen."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        db.record_scrape([v1], {"V001": "new"})
        
        db.mark_seen("V001")
        
        seen = db.get_all_seen()
        assert len(seen) == 1
        assert seen[0].id == "V001"
        assert seen[0].seen is True

    def test_get_all_seen(self, db):
        """Should return all seen vehicles."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        v2 = Vehicle(**SAMPLE_VEHICLE_2)
        db.record_scrape([v1], {"V001": "new"})
        db.record_scrape([v2], {"V002": "new"})
        
        db.mark_seen("V001")
        db.mark_seen("V002")
        
        seen = db.get_all_seen()
        assert len(seen) == 2

    def test_get_history(self, db):
        """Should query history with filters."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        v2 = Vehicle(**SAMPLE_VEHICLE_2)
        db.record_scrape([v1], {"V001": "new"})
        db.record_scrape([v2], {"V002": "new"})
        
        # Query all
        all_records = db.get_history()
        assert len(all_records) == 2
        
        # Query by province
        madrid_records = db.get_history(province=28)
        assert len(madrid_records) == 1
        assert madrid_records[0].cod_provincia == 28
        
        # Query by type
        turismo_records = db.get_history(tipo=101)
        assert len(turismo_records) == 1
        assert turismo_records[0].tipo == 101

    def test_get_stats(self, db):
        """Should return correct statistics."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        v2 = Vehicle(**SAMPLE_VEHICLE_2)
        db.record_scrape([v1], {"V001": "new"})
        db.record_scrape([v2], {"V002": "new"})
        
        db.mark_seen("V001")
        
        stats = db.get_stats()
        assert stats["total_scrapes"] == 2
        assert stats["total_vehicles"] == 2
        assert stats["notified_vehicles"] == 1

    def test_cleanup_old_scrapes(self, db):
        """Should remove old scrapes and keep only recent ones."""
        # Create 35 scrapes
        for i in range(35):
            v = {**SAMPLE_VEHICLE_1, "id": f"V{i:04d}"}
            vehicle = Vehicle(**v)
            db.record_scrape([vehicle], {f"V{i:04d}": "new"})
        
        # Cleanup keeping 30
        removed = db.cleanup_old_scrapes(keep_scrapes=30)
        
        stats = db.get_stats()
        assert stats["total_scrapes"] == 30
        assert removed > 0


class TestVehicleDeduplicator:
    """Tests for the VehicleDeduplicator."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create a test database."""
        db_path = str(tmp_path / "test_dedup.db")
        return HistoryDB(db_path=db_path)

    @pytest.fixture
    def dedup(self, db):
        return VehicleDeduplicator(db)

    def test_new_vehicle(self, dedup):
        """New vehicle should be detected."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        status_map = dedup.compare([v1])
        assert status_map["V001"] == "new"

    def test_unchanged_vehicle(self, db, dedup):
        """Vehicle seen before should be unchanged."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        db.record_scrape([v1], {"V001": "new"})
        
        status_map = dedup.compare([v1])
        assert status_map["V001"] == "unchanged"

    def test_disappeared_vehicle(self, db, dedup):
        """Vehicle not in current scrape should be disappeared."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        db.record_scrape([v1], {"V001": "new"})
        
        # Compare with empty list - V001 should disappear
        status_map = dedup.compare([])
        assert status_map.get("V001") == "disappeared"

    def test_mixed_status(self, db, dedup):
        """Mixed new, unchanged, and disappeared vehicles."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        v2 = Vehicle(**SAMPLE_VEHICLE_2)
        
        # First scrape: both new
        db.record_scrape([v1], {"V001": "new"})
        
        # Second scrape: V001 unchanged, V002 new
        status_map = dedup.compare([v1, v2])
        
        assert status_map["V001"] == "unchanged"
        assert status_map["V002"] == "new"

    def test_get_new_vehicles(self, db, dedup):
        """Should return only new vehicles."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        v2 = Vehicle(**SAMPLE_VEHICLE_2)
        db.record_scrape([v1], {"V001": "new"})
        
        new = dedup.get_new_vehicles([v1, v2])
        assert len(new) == 1
        assert new[0].id == "V002"

    def test_get_disappeared(self, db, dedup):
        """Should return disappeared vehicles."""
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        v2 = Vehicle(**SAMPLE_VEHICLE_2)
        db.record_scrape([v1, v2], {"V001": "new", "V002": "new"})
        
        # Second scrape without V002 - must pass V002 as disappeared
        v1_updated = Vehicle(**SAMPLE_VEHICLE_1)
        v2_disappeared = Vehicle(**SAMPLE_VEHICLE_2)
        status_map = dedup.compare([v1_updated])  # V001 unchanged, V002 disappeared
        db.record_scrape([v1_updated, v2_disappeared], status_map)  # V002 marked as disappeared
        
        disappeared = dedup.get_disappeared()
        assert len(disappeared) >= 1
        assert disappeared[0].id == "V002"


class TestIntegration:
    """Integration tests for history + dedup + scraper."""

    @pytest.fixture
    def db(self, tmp_path):
        db_path = str(tmp_path / "test_integration.db")
        return HistoryDB(db_path=db_path)

    def test_full_workflow(self, db):
        """Test complete workflow: scrape, dedup, notify, clean."""
        from src.scrapers.aetat import AEATScraper
        from src.filters.vehicle_filters import VehicleFilter
        from src.deduplication import VehicleDeduplicator
        
        dedup = VehicleDeduplicator(db)
        
        # Simulate first scrape
        v1 = Vehicle(**SAMPLE_VEHICLE_1)
        v2 = Vehicle(**SAMPLE_VEHICLE_2)
        
        status_map = dedup.compare([v1, v2])
        assert status_map["V001"] == "new"
        assert status_map["V002"] == "new"
        
        db.record_scrape([v1, v2], status_map)
        
        # Simulate second scrape (same vehicles)
        v1_updated = Vehicle(**SAMPLE_VEHICLE_1)
        v2_updated = Vehicle(**SAMPLE_VEHICLE_2)
        status_map = dedup.compare([v1_updated, v2_updated])
        assert status_map["V001"] == "unchanged"
        assert status_map["V002"] == "unchanged"
        
        db.record_scrape([v1_updated, v2_updated], status_map)
        
        # Verify stats
        stats = db.get_stats()
        assert stats["total_scrapes"] == 2
        assert stats["total_vehicles"] == 4  # 2 scrapes × 2 vehicles
