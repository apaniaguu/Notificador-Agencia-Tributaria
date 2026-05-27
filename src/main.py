"""Main entry point for the AEAT vehicle auction notifier."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

from src.scrapers.aetat import AEATScraper
from src.filters.vehicle_filters import VehicleFilter
from src.output import save_json, save_csv, save_summary
from src.notifications.telegram import TelegramNotifier
from src.database import HistoryDB
from src.deduplication import VehicleDeduplicator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = Path(__file__).parent / "config" / "settings.yaml"


def load_config(path: str | Path) -> dict:
    """Load configuration from YAML."""
    path = Path(path)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    logger.warning("Config not found at %s, using defaults", path)
    return {}


def build_filter(config: dict) -> VehicleFilter:
    """Build a VehicleFilter from config dict."""
    f = config.get("filters", {})
    return VehicleFilter(
        provincia=f.get("provincia"),
        max_dias=f.get("max_dias"),
        tipos=f.get("tipos"),
        min_valoracion=f.get("min_valoracion"),
        max_valoracion=f.get("max_valoracion"),
        combustible=f.get("combustible"),
        uso=f.get("uso"),
    )


def run(config_path: str = "config/settings.yaml", cli_filters: Optional[dict] = None):
    """Run the full scraper pipeline with history and deduplication."""
    config = load_config(config_path)
    scraper_config = config.get("scraper", {})
    output_config = config.get("output", {})
    telegram_config = config.get("telegram", {})
    history_config = config.get("history", {})

    # Build filter
    filt = build_filter(config)
    
    # CLI overrides
    if cli_filters:
        for key in ["provincia", "max_dias", "tipos", "min_valoracion", "max_valoracion", "combustible", "uso"]:
            val = cli_filters.get(key)
            if val is not None:
                setattr(filt, key, val)

    # Initialize database
    db_path = history_config.get("db_path", "data/history.db")
    db = HistoryDB(db_path=db_path)
    deduplicator = VehicleDeduplicator(db)

    # Create scraper
    scraper = AEATScraper(
        url=scraper_config.get("url"),
        timeout=scraper_config.get("timeout", 30),
    )

    # Fetch
    logger.info("=" * 50)
    logger.info("Iniciando scraper de subastas AEAT")
    logger.info("=" * 50)
    
    vehicles = scraper.scrape()
    logger.info("Total vehículos encontrados: %d", len(vehicles))

    # Deduplicate against history
    status_map = deduplicator.compare(vehicles)
    new_vehicles = [v for v in vehicles if status_map.get(v.id) == "new"]
    unchanged_vehicles = [v for v in vehicles if status_map.get(v.id) == "unchanged"]
    disappeared_vehicles = [v for v in vehicles if status_map.get(v.id) == "disappeared"]

    logger.info("Novedades: %d | Sin cambios: %d | Desaparecidos: %d",
                len(new_vehicles), len(unchanged_vehicles), len(disappeared_vehicles))

    # Record scrape in database
    db.record_scrape(vehicles, status_map)

    # Filter against criteria
    filtered = filt.apply(vehicles)
    # Only new vehicles match for notifications
    new_filtered = [v for v in filtered if status_map.get(v.id) == "new"]

    logger.info("Vehículos tras filtrar: %d (nuevos: %d)", len(new_filtered), len(new_filtered))

    # Output - save all filtered vehicles regardless of new/old
    out_dir = Path(output_config.get("directory", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    
    for fmt in output_config.get("formats", ["json", "csv", "summary"]):
        if fmt == "json":
            save_json(new_filtered, out_dir / f"vehiculos_{timestamp}.json")
        elif fmt == "csv":
            save_csv(new_filtered, out_dir / f"vehiculos_{timestamp}.csv")
        elif fmt == "summary":
            save_summary(new_filtered, out_dir / f"resumen_{timestamp}.txt")

    # Telegram notification - only for new matching vehicles
    if telegram_config.get("enabled", False) and telegram_config.get("token"):
        notifier = TelegramNotifier(
            token=telegram_config["token"],
            chat_id=telegram_config["chat_id"],
        )
        try:
            if new_filtered:
                notifier.notify_vehicles(new_filtered)
                # Mark as seen
                for v in new_filtered:
                    db.mark_seen(v.id)
            else:
                logger.info("No new vehicles to notify")
        except Exception as e:
            logger.error("Error enviando notificación Telegram: %s", e)
            notifier.notify_error(str(e))

    # Print summary
    logger.info("")
    logger.info("=== RESUMEN ===")
    logger.info("Total vehículos: %d", len(vehicles))
    logger.info("Novedades: %d", len(new_vehicles))
    logger.info("Sin cambios: %d", len(unchanged_vehicles))
    logger.info("Desaparecidos: %d", len(disappeared_vehicles))
    logger.info("Novedades filtradas: %d", len(new_filtered))
    
    if new_filtered:
        tipos = {}
        for v in new_filtered:
            tipos[v.tipo_descripcion] = tipos.get(v.tipo_descripcion, 0) + 1
        logger.info("Tipos: %s", ", ".join(f"{t}: {c}" for t, c in sorted(tipos.items())))
        
        max_val = max(new_filtered, key=lambda v: v.valoracion)
        logger.info("Más caro: %s (%.2f€)", max_val.marca_modelo, max_val.valoracion)
        
        min_val = min(new_filtered, key=lambda v: v.valoracion)
        logger.info("Más barato: %s (%.2f€)", min_val.marca_modelo, min_val.valoracion)

    # Cleanup old scrapes
    keep_scrapes = history_config.get("keep_scrapes", 30)
    if keep_scrapes > 0:
        removed = db.cleanup_old_scrapes(keep_scrapes)
        if removed > 0:
            logger.info("Limpieza: eliminados %d registros antiguos", removed)

    # Stats
    stats = db.get_stats()
    logger.info("Stats: %d scrapes, %d total vehicles, %d notified",
                stats["total_scrapes"], stats["total_vehicles"], stats["notified_vehicles"])
    
    logger.info("Output directory: %s", out_dir)
    logger.info("=== FIN ===")
    
    return new_filtered


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scraper y notificador de subastas de vehículos AEAT"
    )
    parser.add_argument(
        "-c", "--config",
        default=str(DEFAULT_CONFIG),
        help="Path to config YAML file",
    )
    parser.add_argument(
        "-p", "--provincia",
        type=int,
        default=None,
        help="Filter by province code",
    )
    parser.add_argument(
        "-d", "--max-dias",
        type=int,
        default=None,
        help="Max days until auction ends",
    )
    parser.add_argument(
        "-t", "--tipos",
        type=str,
        default=None,
        help="Comma-separated vehicle tipo codes (e.g. 101,103,104)",
    )
    parser.add_argument(
        "-m", "--min-valoracion",
        type=float,
        default=None,
        help="Minimum valuation in euros",
    )
    parser.add_argument(
        "-M", "--max-valoracion",
        type=float,
        default=None,
        help="Maximum valuation in euros",
    )
    parser.add_argument(
        "-C", "--combustible",
        type=str,
        default=None,
        help="Fuel type (D=Diesel, G=Gasolina, H=Hybrid, E=Electric)",
    )
    parser.add_argument(
        "-u", "--uso",
        type=int,
        default=None,
        help="Usage type (1=Private, 6=Professional, 9=Rental)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cli_filters = {}
    for key in ["provincia", "max_dias", "tipos", "min_valoracion", "max_valoracion", "combustible", "uso"]:
        val = getattr(args, key)
        if val is not None:
            if key == "tipos":
                cli_filters[key] = [int(x) for x in val.split(",")]
            else:
                cli_filters[key] = val

    run(config_path=args.config, cli_filters=cli_filters if cli_filters else None)


if __name__ == "__main__":
    main()
