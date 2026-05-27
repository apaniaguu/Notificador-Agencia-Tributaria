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
    """Run the full scraper pipeline."""
    config = load_config(config_path)
    scraper_config = config.get("scraper", {})
    output_config = config.get("output", {})
    telegram_config = config.get("telegram", {})
    
    # CLI overrides
    if cli_filters:
        for key in ["provincia", "max_dias", "tipos", "min_valoracion", "max_valoracion", "combustible", "uso"]:
            if key in cli_filters and cli_filters[key] is not None:
                scraper_config.setdefault("filters", {})[key] = cli_filters[key]

    # Build filter
    filt = build_filter(config)
    
    # Override with CLI args
    if cli_filters:
        if cli_filters.get("provincia") is not None:
            filt.provincia = cli_filters["provincia"]
        if cli_filters.get("max_dias") is not None:
            filt.max_dias = cli_filters["max_dias"]
        if cli_filters.get("tipos") is not None:
            filt.tipos = cli_filters["tipos"]
        if cli_filters.get("min_valoracion") is not None:
            filt.min_valoracion = cli_filters["min_valoracion"]
        if cli_filters.get("max_valoracion") is not None:
            filt.max_valoracion = cli_filters["max_valoracion"]
        if cli_filters.get("combustible") is not None:
            filt.combustible = cli_filters["combustible"]
        if cli_filters.get("uso") is not None:
            filt.uso = cli_filters["uso"]

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

    # Filter
    filtered = filt.apply(vehicles)
    logger.info("Vehículos tras filtrar: %d", len(filtered))

    # Output
    out_dir = Path(output_config.get("directory", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    
    for fmt in output_config.get("formats", ["json", "csv", "summary"]):
        if fmt == "json":
            save_json(filtered, out_dir / f"vehiculos_{timestamp}.json")
        elif fmt == "csv":
            save_csv(filtered, out_dir / f"vehiculos_{timestamp}.csv")
        elif fmt == "summary":
            save_summary(filtered, out_dir / f"resumen_{timestamp}.txt")

    # Telegram notification
    if telegram_config.get("enabled", False) and telegram_config.get("token"):
        notifier = TelegramNotifier(
            token=telegram_config["token"],
            chat_id=telegram_config["chat_id"],
        )
        try:
            notifier.notify_vehicles(filtered)
        except Exception as e:
            logger.error("Error enviando notificación Telegram: %s", e)
            notifier.notify_error(str(e))

    # Print summary
    logger.info("")
    logger.info("=== RESUMEN ===")
    logger.info("Total vehículos: %d", len(vehicles))
    logger.info("Vehículos filtrados: %d", len(filtered))
    
    if filtered:
        tipos = {}
        for v in filtered:
            tipos[v.tipo_descripcion] = tipos.get(v.tipo_descripcion, 0) + 1
        logger.info("Tipos: %s", ", ".join(f"{t}: {c}" for t, c in sorted(tipos.items())))
        
        max_val = max(filtered, key=lambda v: v.valoracion)
        logger.info("Más caro: %s (%.2f€)", max_val.marca_modelo, max_val.valoracion)
        
        min_val = min(filtered, key=lambda v: v.valoracion)
        logger.info("Más barato: %s (%.2f€)", min_val.marca_modelo, min_val.valoracion)

    logger.info("Output directory: %s", out_dir)
    logger.info("=== FIN ===")
    
    return filtered


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
