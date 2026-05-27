# Proposal: Scrape Vehículos AEAT

## Problem
La AEAT publica subastas de vehículos en una web que no ofrece API pública. Necesitamos un scraper robusto que extraiga los datos de las subastas de vehículos de forma programática para poder notificar al usuario.

## Solution
Crear un scraper en Python que:
1. Descargue el archivo JS `bienes.js` de la AEAT (fuente de datos estructurada)
2. Parsee el array `vehiculosSubasta` 
3. Extraiga los campos relevantes: id, matricula, marcaModelo, valoracion, finSubasta, codProvincia, bastidor, plazas, cilindrada, años
4. Permita filtrar por provincia, fecha de fin, tipo de vehículo
5. Genere alertas/notificaciones para vehículos que cumplan criterios configurables

## Why this approach
- El archivo `data2/bienes.js` es una fuente de datos estructurada y estable (actualizada diariamente por la AEAT)
- Más fiable que hacer scraping del HTML que puede cambiar
- No requiere autenticación ni manejo de sesiones

## Key Decisions
- Python 3.11+ para el scraper
- Uso de `requests` + `re` para parsear el JS (sin dependencias pesadas)
- Almacenamiento local en JSON/SQLite para historial
- Notificaciones por Telegram (integración futura)

## Success Criteria
- [ ] Scraper extrae correctamente todos los vehículos del archivo JS
- [ ] Se pueden filtrar por provincia, fecha máxima de subasta, tipo de vehículo
- [ ] Se genera un informe CSV/JSON con los resultados
- [ ] Se integra con Telegram para notificaciones
- [ ] Al menos 200 vehículos scrapeados con éxito
