# Notificador Agencia Tributaria - Primera versión

## 📋 Descripción
Aplicación para scrapear y notificar subastas de vehículos de la Agencia Tributaria (AEAT).

## 🎯 Funcionalidades
- Scrapeo de vehículos en subasta de la AEAT
- Notificación a Telegram con resumen de vehículos
- Historial de scrapes con deduplicación
- WebApp simple para ver resultados

## ⚙️ Configuración
```yaml
# config/settings.yaml
telegram:
  enabled: true
  token: "8870806330:***"
  chat_id: "753321710"
```

## 📁 Estructura
```
Notificador-Agencia-Tributaria/
├── config/
│   └── settings.yaml
├── src/
│   ├── scrapers/
│   │   └── aetat.py
│   ├── database.py
│   ├── models/
│   │   └── history.py
│   ├── webhook/
│   │   └── telegram.py
│   └── webapp/
│       └── app.py
├── data/
│   └── history.db
├── openspec/
├── tests/
│   ├── test_scraper.py
│   ├── test_history.py
│   └── test_telegram.py
└── README.md
```

## 🚀 Uso

### Scrapeo
```bash
cd /home/apaniaguu/Notificador-Agencia-Tributaria
source venv/bin/activate

# Test scrapeo
python -c "from src.scrapers.aetat import AEATScraper; s=AEATScraper(); print(len(s.scrape()), 'vehículos')"

# Enviar notificación
python -c "
from src.scrapers.aetat import AEATScraper
from src.webhook.telegram import TelegramWebhook

scraper = AEATScraper()
vehicles = scraper.scrape()

webhook = TelegramWebhook(
    token='8870806330:***',
    chat_id=753321710,
)

webhook.notify_vehicles(vehicles)
"
```

### WebApp
```bash
cd /home/apaniaguu/Notificador-Agencia-Tributaria
source venv/bin/activate
python src/webapp/app.py
```

## 📊 Salida del mensaje
```
🚗 TODO TERRENO MERCEDES ML 320

📊 Valoración: 12,500.00€
⚖️ Cargas: 0.00€
💰 Neto: 12,500.00€

📁 Tipo: Turismos
🔢 Matrícula: Sin matrícula
📅 Fin subasta: 2026-06-15

📍 Provincia: 28
```

## 🧪 Tests
```bash
pytest tests/
```

## 📝 Historial
- v0.1.0 - Primera versión con webhook Telegram
