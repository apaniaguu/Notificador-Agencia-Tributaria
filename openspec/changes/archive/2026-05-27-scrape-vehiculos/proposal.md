# Change: Scrape Vehículos AEAT

## Why
La AEAT publica subastas de vehículos en una web sin API pública. Necesitamos un scraper robusto que extraiga los datos de forma programática para poder notificar al usuario sobre oportunidades de compra.

## What Changes
- Scraper en Python que descarga y parsea datos del archivo JS público `bienes.js` de la AEAT
- Modelos Pydantic para vehículos con mapeo de tipos y campos
- Filtros configurables por provincia, tipo, fecha, valoración, combustible, uso
- Salida en JSON, CSV y resumen texto plano
- Módulo de notificaciones por Telegram
- CLI con argparse para ejecutar con filtros por línea de comandos
- Configuración YAML para personalizar comportamiento
- 19 tests unitarios

## Impact
- `src/models/vehicle.py` - Modelo de datos para vehículos
- `src/scrapers/aetat.py` - Scraper de la AEAT
- `src/filters/vehicle_filters.py` - Filtros configurables
- `src/output.py` - Exportación JSON/CSV/Summary
- `src/notifications/telegram.py` - Notificaciones Telegram
- `src/main.py` - Entry point CLI
- `config/settings.yaml` - Configuración
- `tests/test_scraper.py` - Tests unitarios
