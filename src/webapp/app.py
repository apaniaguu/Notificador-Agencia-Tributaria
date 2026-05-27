from flask import Flask, render_template_string, jsonify
from pathlib import Path
from src.scrapers.aetat import AEATScraper
from src.database import HistoryDB
from src.webhook.telegram import TelegramWebhook

app = Flask(__name__)
TEMPLATES_DIR = Path('/home/apaniaguu/Notificador-Agencia-Tributaria/src/webapp/templates')
TEMPLATES_DIR.mkdir(exist_ok=True)


@app.template_filter('currency')
def format_currency(value):
    """Format number as EUR currency with 2 decimals."""
    if value is None:
        return "0,00 €"
    try:
        num = float(value)
        return f"{num:,.2f} €"
    except (ValueError, TypeError):
        return "0,00 €"


@app.route('/')
def index():
    """Vista principal con lista de vehículos"""
    scraper = AEATScraper()
    vehicles = scraper.scrape()
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subastas de Vehículos - AEAT</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; margin-bottom: 20px; }
        .vehicle-card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .vehicle-card h2 { color: #2563eb; margin-bottom: 15px; font-size: 1.2em; }
        .photo-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; margin-bottom: 15px; }
        .photo { width: 100%; height: 100px; object-fit: cover; border-radius: 4px; cursor: pointer; }
        .photo:hover { opacity: 0.8; }
        .info { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 10px; }
        .info span { font-weight: 600; color: #666; }
        .info strong { color: #333; }
        @media (max-width: 768px) { .photo-grid { grid-template-columns: repeat(3, 1fr); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 Subastas de Vehículos - AEAT</h1>
        {% if vehicles %}
            {% for vehicle in vehicles %}
            <div class="vehicle-card">
                <h2>🚗 {{ vehicle.marca_modelo }}</h2>
                <div class="photo-grid">
                    {% for photo_url in vehicle.fotos[:5] %}
                    {% if photo_url %}
                    <img src="{{ photo_url }}" class="photo" alt="Foto {{ loop.index }}">
                    {% endif %}
                    {% endfor %}
                </div>
                <div class="info">
                    <span>💰 Valoración:</span> <strong>{{ vehicle.valoracion | currency }}</strong>
                    <span>⚖️ Cargas:</span> <strong>{{ vehicle.cargas | currency }}</strong>
                    <span>💰 Neto:</span> <strong>{{ vehicle.valor_neto | currency }}</strong>
                    <span>📅 Fin:</span> <strong>{{ vehicle.fin_subasta }}</strong>
                </div>
                <div class="info">
                    <span>📁 Tipo:</span> <strong>{{ vehicle.tipo_descripcion }}</strong>
                    <span>🔢 Matrícula:</strong> <strong>{{ vehicle.matricula or 'Sin matrícula' }}</strong>
                    <span>📍 Provincia:</strong> <strong>{{ vehicle.cod_provincia }}</strong>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <p class="loading">Cargando datos...</p>
        {% endif %}
    </div>
</body>
</html>
    ''', vehicles=vehicles)


@app.route('/stats')
def stats():
    """Estadísticas de scrapes"""
    db = HistoryDB()
    stats = db.get_stats()
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estadísticas - AEAT</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .stats-card { background: white; border-radius: 8px; padding: 30px; margin-bottom: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stats-card h2 { color: #2563eb; margin-bottom: 20px; }
        .stat { font-size: 3em; font-weight: bold; color: #2563eb; }
        .stat-label { color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Estadísticas</h1>
        <div class="stats-card">
            <h2>Total Scrapes</h2>
            <div class="stat">{{ total_scrapes }}</div>
            <div class="stat-label">Ejecuciones</div>
        </div>
        <div class="stats-card">
            <h2>Total Vehículos</h2>
            <div class="stat">{{ total_vehicles }}</div>
            <div class="stat-label">Vehículos únicos</div>
        </div>
    </div>
</body>
</html>
    ''', total_scrapes=stats['total_scrapes'], total_vehicles=stats['total_vehicles'])


@app.route('/logs')
def logs():
    """Últimos logs de notificaciones"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Logs - AEAT</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        pre { background: white; border-radius: 8px; padding: 20px; overflow-x: auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Logs de Notificaciones</h1>
        <pre>
<div id="logs">Cargando logs...</div>
        </pre>
    </div>
    <script>
        fetch('/api/logs')
            .then(r => r.json())
            .then(data => {
                document.getElementById('logs').innerHTML = data.map(l => 
                    `<div>${l}</div>`
                ).join('');
            });
    </script>
</body>
</html>
    ''')


@app.route('/api/logs')
def api_logs():
    """API para obtener logs de notificaciones"""
    db = HistoryDB()
    all_vehicles = db.get_all_seen(limit=100)
    logs = []
    for v in all_vehicles:
        log = f"🚗 {v.marca_modelo} - {v.fin_subasta}"
        logs.append(log)
    return jsonify(logs)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
