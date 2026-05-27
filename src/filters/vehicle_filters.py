"""Filters for vehicle auction data."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from src.models.vehicle import Vehicle

logger = logging.getLogger(__name__)


class VehicleFilter:
    """Filter vehicles based on configurable criteria."""

    def __init__(
        self,
        provincia: Optional[int] = None,
        max_dias: Optional[int] = None,
        tipos: Optional[list[int]] = None,
        min_valoracion: Optional[float] = None,
        max_valoracion: Optional[float] = None,
        combustible: Optional[str] = None,
        uso: Optional[int] = None,
    ):
        self.provincia = provincia
        self.max_dias = max_dias
        self.tipos = tipos
        self.min_valoracion = min_valoracion
        self.max_valoracion = max_valoracion
        self.combustible = combustible
        self.uso = uso

    def apply(self, vehicles: list[Vehicle]) -> list[Vehicle]:
        """Apply all filters to a list of vehicles.
        
        Returns vehicles matching ALL criteria (AND logic).
        """
        filtered = vehicles

        if self.provincia is not None:
            before = len(filtered)
            filtered = [v for v in filtered if v.cod_provincia == self.provincia]
            logger.info("Province filter: %d → %d", before, len(filtered))

        if self.max_dias is not None:
            before = len(filtered)
            filtered = [
                v for v in filtered
                if v.dias_hasta_fin is not None and v.dias_hasta_fin <= self.max_dias
            ]
            logger.info("Max days filter: %d → %d", before, len(filtered))

        if self.tipos is not None:
            before = len(filtered)
            filtered = [v for v in filtered if v.tipo in self.tipos]
            logger.info("Tipo filter: %d → %d", before, len(filtered))

        if self.min_valoracion is not None:
            before = len(filtered)
            filtered = [v for v in filtered if v.valoracion >= self.min_valoracion]
            logger.info("Min val filter: %d → %d", before, len(filtered))

        if self.max_valoracion is not None:
            before = len(filtered)
            filtered = [v for v in filtered if v.valoracion <= self.max_valoracion]
            logger.info("Max val filter: %d → %d", before, len(filtered))

        if self.combustible is not None:
            before = len(filtered)
            filtered = [
                v for v in filtered
                if v.combustible and v.combustible.upper() == self.combustible.upper()
            ]
            logger.info("Combustible filter: %d → %d", before, len(filtered))

        if self.uso is not None:
            before = len(filtered)
            filtered = [v for v in filtered if v.uso == self.uso]
            logger.info("Uso filter: %d → %d", before, len(filtered))

        return filtered

    def matches(self, vehicle: Vehicle) -> bool:
        """Check if a single vehicle matches all criteria."""
        filtered = self.apply([vehicle])
        return len(filtered) == 1
