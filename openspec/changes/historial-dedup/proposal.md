# Change: Historial y Deduplicación

## Why
El scraper actual es estático: cada ejecución devuelve los mismos resultados. Necesitamos persistencia para:
- Detectar **novedades** (vehículos que aparecen nuevos entre scrapes)
- Evitar **duplicados** (no notificar el mismo vehículo dos veces)
- Mantener un **historial** consultable de todas las subastas pasadas

Sin esto, el sistema no puede funcionar como notificador autónomo.

## What Changes
- SQLite database para persistencia de vehículos scrapeados
- Registro con timestamp de cada scrapeo
- Detección de vehículos nuevos vs ya vistos
- Detección de vehículos desaparecidos (subasta cancelada/removida)
- Estado de "visto" por notificación Telegram
- Consulta de historial con filtros por fecha, provincia, tipo
- Configuración de retención (cuántos scrapes guardar)

## Impact
- `src/database.py` - Capa de base de datos SQLite
- `src/models/history.py` - Modelos de historial
- `src/main.py` - Integración con el flujo principal
- `config/settings.yaml` - Nuevos campos de retención
- Actualización de specs de vehicle-scraper
