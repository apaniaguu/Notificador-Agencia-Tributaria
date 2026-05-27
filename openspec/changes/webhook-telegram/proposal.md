# Proposal: Webhook para Telegram con fotos y página web

## Problem
El scraper actual solo descarga los datos del JSON, pero no las fotos de los vehículos. Necesitamos:
1. Descargar las fotos de los vehículos desde la AEAT
2. Webhook para Telegram que envíe notificaciones con fotos, marca, precio y ubicación
3. Página web con listado de todos los vehículos
4. Almacenamiento de fotos en local

## Solution
Crear un sistema completo con:
1. **Imagewriter**: Un scraper que descarga las fotos de los vehículos
2. **Webhook Telegram**: Un webhook que recibe datos y envía notificaciones con fotos
3. **Página web**: Una app que muestra el listado de vehículos con fotos
4. **Storage**: Almacenar fotos en local o cloud

## Why this approach
- La fotos están disponibles en el JSON de la AEAT (fotos: ["001.jpg", "002.jpg", ...])
- Usar Flask para la página web (simple, rápido, fácil de desplegar)
- Usar Telegram Bot API para el webhook
- Actualizar las fotos desde la AEAT al hacer scrape

## Key Decisions
- Fotos: se descargan desde la AEAT y se guardan en local
- Webhook: Flask endpoint que recibe datos y envía a Telegram
- Página web: Flask app con template de listado
- Fotos: se guardan en ~/Notificador-Agencia-Tributaria/photos/

## Success Criteria
- [ ] Imagewriter descarga fotos correctamente
- [ ] Webhook Telegram envía notificaciones con fotos
- [ ] Página web muestra listado de vehículos con fotos
- [ ] Todas las funcionalidades integradas
