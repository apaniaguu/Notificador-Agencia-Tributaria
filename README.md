# Notificador Agencia Tributaria

Scraper y notificador de subastas de vehículos de la Agencia Tributaria española (AEAT).

## Descripción

Este proyecto scrapea las subastas de vehículos publicadas por la AEAT en su sede electrónica y genera alertas/notificaciones basadas en filtros configurables.

## Funcionalidades

- **Scraping**: Descarga de datos de subastas desde el archivo JS público de la AEAT
- **Filtrado**: Por provincia, tipo de vehículo, fecha de fin, valoración, combustible, uso
- **Salida**: JSON, CSV y resumen en texto plano
- **Notificaciones**: Integración con Telegram para alertas en tiempo real
- **Historial**: Almacenamiento local de scrapes anteriores para detección de novedades

## Instalación

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -e .
```

## Uso

```bash
# Ejecución básica (usa config/settings.yaml)
python -m src.main

# Con filtros por línea de comandos
python -m src.main --provincia 28 --max-dias 30
python -m src.main --tipos 101,103 --min-valoracion 5000

# Con config personalizada
python -m src.main -c mi_config.yaml
```

## Configuración

Edita `config/settings.yaml` para personalizar filtros, salida y notificaciones Telegram.

### Filtros disponibles

| Filtro | Tipo | Descripción |
|--------|------|-------------|
| `provincia` | int | Código de provincia (2=Almería, 28=Madrid, etc.) |
| `max_dias` | int | Máximo de días hasta fin de subasta |
| `tipos` | list[int] | Tipos de vehículo (101=Turismo, 103=Furgoneta, etc.) |
| `min_valoracion` | float | Valoración mínima en € |
| `max_valoracion` | float | Valoración máxima en € |
| `combustible` | str | D=Diésel, G=Gasolina, H=Híbrido, E=Eléctrico |
| `uso` | int | 1=Particular, 6=Profesional, 9=Alquiler |

## Estructura del proyecto

```
src/
├── models/          # Modelos de datos (Vehicle)
├── filters/         # Filtros configurables
├── scrapers/        # Scraper de la AEAT
├── notifications/   # Notificaciones (Telegram)
├── output.py        # Exportación JSON/CSV/Summary
└── main.py          # Entry point CLI
tests/               # Tests unitarios
config/              # Configuración YAML
output/              # Resultados generados
```

## OpenSpec

Este proyecto sigue el flujo de trabajo OpenSpec para desarrollo spec-driven.
Los cambios se documentan en `openspec/changes/`.

## Licencia

MIT
