# Tasks: Scrape Vehículos AEAT

## Task 1: Project setup
- **Files:** `pyproject.toml`, `README.md`, `.gitignore`, `requirements.txt`
- Create Python project structure

## Task 2: Data fetching module
- **Files:** `src/scrapers/aetat.py`
- Create the AEAT data fetcher that downloads bienes.js and extracts vehiculosSubasta

## Task 3: Data parsing module
- **Files:** `src/models/vehicle.py`
- Create vehicle data model with type mappings and field parsing

## Task 4: Filtering module
- **Files:** `src/filters/vehicle_filters.py`
- Create filter functions for province, date, type, valuation

## Task 5: Main scraper entry point
- **Files:** `src/main.py`
- CLI entry point that orchestrates fetch → parse → filter → output

## Task 6: Output module (JSON/CSV)
- **Files:** `src/output.py`
- Generate JSON and CSV output files

## Task 7: Telegram notification module
- **Files:** `src/notifications/telegram.py`
- Telegram bot integration for sending alerts

## Task 8: Configuration
- **Files:** `config/settings.yaml`
- YAML configuration for filters, provinces, Telegram token

## Task 9: Testing
- **Files:** `tests/test_scraper.py`
- Unit tests for the scraper logic

## Task 10: Final commit and archive
- **Files:** (various)
- Archive the change and commit everything
