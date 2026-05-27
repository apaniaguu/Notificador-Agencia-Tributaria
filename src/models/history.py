"""History models for vehicle deduplication and tracking."""

from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class VehicleRecord(BaseModel):
    """A single vehicle record in the history database."""

    id: str = Field(description="Unique vehicle ID")
    scrape_id: int = Field(description="Scrape batch ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = Field(description="new, unchanged, or disappeared")
    # All vehicle fields duplicated for history queries
    subasta: str = ""
    fin_subasta: str = ""
    cod_provincia: int = 0
    valoracion: float = 0.0
    cargas: float = 0.0
    tipo: int = 0
    matricula: str = ""
    bastidor: str = ""
    marca_modelo: str = ""
    plazas: Optional[int] = None
    combustible: str = ""
    cilindrada: Optional[int] = None
    años: Optional[float] = None
    unico_propietario: int = 0
    uso: Optional[int] = None
    fotos_count: int = 0
    seen: bool = Field(default=False, description="Whether notification was sent")

    class Config:
        populate_by_name = True


class ScrapeEvent(BaseModel):
    """A scrape event (batch) that groups vehicle records."""

    scrape_id: int = Field(description="Auto-incrementing batch ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    total_vehicles: int = 0
    new_vehicles: int = 0
    unchanged_vehicles: int = 0
    disappeared_vehicles: int = 0
    error: str = ""

    class Config:
        populate_by_name = True
