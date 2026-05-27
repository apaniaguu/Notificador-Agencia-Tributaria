# Notificador AEAT - Web App

Simple web app para visualizar las subastas de vehículos de la AEAT.

## 🚀 Cómo usar

```bash
# Iniciar la web app
python src/webapp/app.py

# O ejecutar con uvicorn (más rápido)
uvicorn src/webapp/app:app --reload
```

## 📍 Endpoints

- `/` - Vista principal con lista de vehículos
- `/stats` - Estadísticas de scrapes
- `/logs` - Últimos logs de notificaciones

## 🎨 Características

- 📱 Diseño responsive
- 🖼️ Imágenes de los vehículos
- 📊 Información completa (valoración, cargas, neto, etc.)
- 📈 Estadísticas de scrapes
- 🔄 Historial en tiempo real
