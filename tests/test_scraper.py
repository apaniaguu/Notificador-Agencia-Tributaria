"""Tests for the AEAT vehicle auction notifier."""

from __future__ import annotations

import json
import pytest
from datetime import date

from src.models.vehicle import Vehicle
from src.filters.vehicle_filters import VehicleFilter
from src.scrapers.aetat import AEATScraper


# Test fixture data
SAMPLE_VEHICLE = {
    "id": "0803828456500020",
    "subasta": "SUB-AT-2026-26R0886002035",
    "finSubasta": "2026-06-08",
    "codProvincia": 4,
    "valoracion": 12112.0,
    "cargas": 0,
    "tipo": 101,
    "matricula": "0167FNW",
    "bastidor": "WDC1641221A190733",
    "marcaModelo": "TODO TERRENO MERCEDES ML 320",
    "plazas": 5,
    "combustible": "D",
    "cilindrada": 2987,
    "años": 19.08,
    "unicoPropietario": 0,
    "uso": 1,
    "fotos": ["001.jpg", "002.jpg"],
}

SAMPLE_VEHICLE_2 = {
    "id": "0390268881300013",
    "subasta": "SUB-AT-2026-26R4686002015",
    "finSubasta": "2026-06-08",
    "codProvincia": 3,
    "valoracion": 6802.0,
    "cargas": 0,
    "tipo": 104,
    "matricula": "1797JPG",
    "bastidor": "VSKCTND23U0019076",
    "marcaModelo": "CAMION CAJA NISSAN NISSAN NP300 NAVARA",
    "plazas": 5,
    "combustible": "D",
    "cilindrada": 2298,
    "años": 10.0,
    "unicoPropietario": 0,
    "uso": 1,
    "fotos": ["001.jpg"],
}

SAMPLE_VEHICLE_3 = {
    "id": "0895936284600027",
    "subasta": "SUB-AT-2026-26R0886002019",
    "finSubasta": "2026-06-08",
    "codProvincia": 4,
    "valoracion": 13472.5,
    "cargas": 0,
    "tipo": 103,
    "matricula": "1902KRY",
    "bastidor": "VF3YB2MFB12J12031",
    "marcaModelo": "FURGONETA PEUGEOT BOXER FURG N PACK 333",
    "plazas": 3,
    "combustible": "D",
    "cilindrada": 1997,
    "años": 7.49,
    "unicoPropietario": 1,
    "uso": 1,
    "fotos": ["001.jpg", "002.jpg", "003.jpg", "004.jpg", "005.jpg", "006.jpg", "007.jpg"],
}


class TestVehicleModel:
    """Tests for the Vehicle model."""

    def test_create_vehicle(self):
        v = Vehicle(**SAMPLE_VEHICLE)
        assert v.id == "0803828456500020"
        assert v.tipo_descripcion == "Turismo"
        assert v.combustible_descripcion == "Diésel"
        assert v.uso_descripcion == "Particular"
        assert v.valor_neto == 12112.0

    def test_tipo_mapping(self):
        v = Vehicle(**SAMPLE_VEHICLE)
        assert v.tipo_descripcion == "Turismo"
        
        camion = {**SAMPLE_VEHICLE, "tipo": 104}
        v2 = Vehicle(**camion)
        assert v2.tipo_descripcion == "Camión"

    def test_dias_hasta_fin(self):
        v = Vehicle(**SAMPLE_VEHICLE)
        dias = v.dias_hasta_fin
        assert dias is not None
        # Should be a reasonable number of days from today
        assert 0 <= dias <= 365

    def test_to_csv_row(self):
        v = Vehicle(**SAMPLE_VEHICLE)
        row = v.to_csv_row()
        assert row["id"] == "0803828456500020"
        assert "Turismo" in row["tipo"]
        assert "0167FNW" in row["matricula"]

    def test_partial_vehicle(self):
        """Vehicle with minimal fields should still work."""
        minimal = {
            "id": "test123",
            "subasta": "SUB-TEST",
            "finSubasta": "2026-12-31",
            "codProvincia": 28,
            "valoracion": 1000.0,
            "cargas": 0,
            "tipo": 101,
            "marcaModelo": "Test Car",
            "unicoPropietario": 0,
        }
        v = Vehicle(**minimal)
        assert v.id == "test123"
        assert v.bastidor is None
        assert v.plazas is None

    def test_vehicle_serialization(self):
        v = Vehicle(**SAMPLE_VEHICLE)
        data = v.model_dump(by_alias=True, exclude_none=True)
        assert "id" in data
        assert "marcaModelo" in data


class TestVehicleFilter:
    """Tests for the VehicleFilter."""

    @pytest.fixture
    def vehicles(self):
        return [
            Vehicle(**SAMPLE_VEHICLE),       # provincia 4, tipo 101
            Vehicle(**SAMPLE_VEHICLE_2),     # provincia 3, tipo 104
            Vehicle(**SAMPLE_VEHICLE_3),     # provincia 4, tipo 103
        ]

    def test_filter_by_provincia(self, vehicles):
        filt = VehicleFilter(provincia=4)
        result = filt.apply(vehicles)
        assert len(result) == 2
        assert all(v.cod_provincia == 4 for v in result)

    def test_filter_by_tipo(self, vehicles):
        filt = VehicleFilter(tipos=[101])
        result = filt.apply(vehicles)
        assert len(result) == 1
        assert result[0].tipo == 101

    def test_filter_multiple(self, vehicles):
        filt = VehicleFilter(provincia=4, tipos=[101])
        result = filt.apply(vehicles)
        assert len(result) == 1
        assert result[0].id == SAMPLE_VEHICLE["id"]

    def test_no_match(self, vehicles):
        filt = VehicleFilter(provincia=999)
        result = filt.apply(vehicles)
        assert len(result) == 0

    def test_matches_single(self, vehicles):
        filt = VehicleFilter(provincia=4)
        assert filt.matches(vehicles[0])
        assert not filt.matches(vehicles[1])

    def test_filter_by_valoracion(self, vehicles):
        filt = VehicleFilter(min_valoracion=10000, max_valoracion=15000)
        result = filt.apply(vehicles)
        assert all(10000 <= v.valoracion <= 15000 for v in result)

    def test_filter_by_combustible(self, vehicles):
        filt = VehicleFilter(combustible="D")
        result = filt.apply(vehicles)
        assert all(v.combustible and v.combustible.upper() == "D" for v in result)


class TestAEATScraper:
    """Tests for the AEATScraper."""

    def test_scraper_initialization(self):
        scraper = AEATScraper()
        assert scraper.url is not None
        assert scraper.timeout == 30

    def test_scraper_custom_url(self):
        scraper = AEATScraper(url="http://example.com/test.js")
        assert scraper.url == "http://example.com/test.js"


class TestOutput:
    """Tests for the output module."""

    def test_save_json(self, tmp_path):
        from src.output import save_json
        v = Vehicle(**SAMPLE_VEHICLE)
        path = save_json([v], tmp_path / "test.json")
        assert path.exists()
        data = json.loads(path.read_text())
        assert len(data) == 1
        assert data[0]["id"] == "0803828456500020"

    def test_save_csv(self, tmp_path):
        from src.output import save_csv
        v = Vehicle(**SAMPLE_VEHICLE)
        path = save_csv([v], tmp_path / "test.csv")
        assert path.exists()
        content = path.read_text()
        assert "id" in content
        assert "0803828456500020" in content

    def test_save_empty(self, tmp_path):
        from src.output import save_json, save_csv
        json_path = save_json([], tmp_path / "empty.json")
        csv_path = save_csv([], tmp_path / "empty.csv")
        assert json_path.exists()
        assert csv_path.exists()


class TestConfig:
    """Tests for config loading."""

    def test_default_config_exists(self):
        from pathlib import Path
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        assert config_path.exists()
