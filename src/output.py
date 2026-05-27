"""Output module - JSON and CSV export."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Optional

from src.models.vehicle import Vehicle

logger = logging.getLogger(__name__)


def save_json(vehicles: list[Vehicle], path: str | Path) -> Path:
    """Save vehicles as JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [v.to_csv_row() for v in vehicles]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved %d vehicles to JSON: %s", len(vehicles), path)
    return path


def save_csv(vehicles: list[Vehicle], path: str | Path) -> Path:
    """Save vehicles as CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [v.to_csv_row() for v in vehicles]
    if not rows:
        logger.warning("No vehicles to save")
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        return path

    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Saved %d vehicles to CSV: %s", len(vehicles), path)
    return path


def save_summary(vehicles: list[Vehicle], path: str | Path) -> Path:
    """Save a human-readable summary."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("=== Resumen de vehículos AEAT ===\n\n")
        f.write(f"Total vehículos: {len(vehicles)}\n\n")
        
        # Por tipo
        tipos = {}
        for v in vehicles:
            tipos[v.tipo_descripcion] = tipos.get(v.tipo_descripcion, 0) + 1
        f.write("Por tipo:\n")
        for t, c in sorted(tipos.items()):
            f.write(f"  {t}: {c}\n")
        
        # Por provincia
        provs = {}
        for v in vehicles:
            provs[v.cod_provincia] = provs.get(v.cod_provincia, 0) + 1
        f.write("\nPor provincia:\n")
        for p, c in sorted(provs.items()):
            f.write(f"  {p}: {c}\n")
        
        # Top 10 más caros
        f.write("\nTop 10 por valoración:\n")
        top = sorted(vehicles, key=lambda v: v.valoracion, reverse=True)[:10]
        for i, v in enumerate(top, 1):
            f.write(f"  {i}. {v.marca_modelo} - {v.valoracion:,.2f}€ "
                   f"(fin: {v.fin_subasta})\n")
        
        # Próximos a vencer (menos de 7 días)
        f.write("\nPróximos a vencer (< 7 días):\n")
        urgentes = [v for v in vehicles if v.dias_hasta_fin is not None and v.dias_hasta_fin < 7]
        if urgentes:
            for v in sorted(urgentes, key=lambda v: v.dias_hasta_fin or 9999):
                f.write(f"  {v.marca_modelo} - {v.dias_hasta_fin} días - "
                       f"{v.valoracion:,.2f}€\n")
        else:
            f.write("  Ninguno\n")
    
    logger.info("Saved summary to: %s", path)
    return path
