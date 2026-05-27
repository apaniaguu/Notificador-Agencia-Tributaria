"""Web application for vehicle auction listings."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, render_template_string, jsonify, send_from_directory

logger = logging.getLogger(__name__)

# HTML template for vehicle listings
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subastas de Vehículos AEAT</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 20px 0;
            text-align: center;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .vehicle-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .vehicle-card {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .vehicle-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .vehicle-photo {
            width: 100%;
            height: 200px;
            object-fit: cover;
            background: #eee;
        }
        .vehicle-info {
            padding: 20px;
        }
        .vehicle-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        .vehicle-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }
        .detail {
            display: flex;
            flex-direction: column;
        }
        .detail-label {
            font-size: 0.8em;
            color: #666;
            text-transform: uppercase;
        }
        .detail-value {
            font-size: 1em;
            font-weight: 500;
        }
        .price {
            color: #27ae60;
            font-size: 1.2em;
            font-weight: bold;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 500;
        }
        .badge-new {
            background: #27ae60;
            color: white;
        }
        .badge-unchanged {
            background: #f39c12;
            color: white;
        }
        .no-photo {
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f0f0f0;
            color: #999;
            font-size: 3em;
        }
        .filters {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .filter-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .filter-group select,
        .filter-group input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }
        .last-update {
            text-align: center;
            color: #666;
            padding: 20px 0;
            border-top: 1px solid #eee;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <header>
        <h1>🚗 Subastas de Vehículos AEAT</h1>
        <p class="subtitle">Notificador de subastas de vehículos confiscados</p>
    </header>

    <div class="container">
        {% if vehicles %}
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ vehicles|length }}</div>
                <div class="stat-label">Vehículos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ total_valores|sum|format_currency }}</div>
                <div class="stat-label">Valoración Total</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ tipos|length }}</div>
                <div class="stat-label">Tipos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ provincias|length }}</div>
                <div class="stat-label">Provincias</div>
            </div>
        </div>

        <div class="filters">
            <h3>Filtros</h3>
            <div class="filter-group">
                <select id="typeFilter">
                    <option value="">Todos los tipos</option>
                    {% for tipo in tipos|sort %}
                    <option value="{{ tipo }}">{{ tipo }}</option>
                    {% endfor %}
                </select>
                <input type="number" id="minPrice" placeholder="Precio mínimo" />
                <input type="number" id="maxPrice" placeholder="Precio máximo" />
                <button onclick="applyFilters()">Filtrar</button>
            </div>
        </div>

        <div class="vehicle-grid">
            {% for vehicle in vehicles %}
            <div class="vehicle-card" data-type="{{ vehicle.tipo_descripcion }}" data-price="{{ vehicle.valoracion }}">
                {% if vehicle.fotos %}
                <img src="/photos/{{ vehicle.id }}/{{ vehicle.fotos[0] }}" 
                     alt="{{ vehicle.marca_modelo }}" 
                     class="vehicle-photo"
                     onerror="this.parentElement.querySelector('.vehicle-photo').style.display='none'; this.style.display='block';">
                {% else %}
                <div class="vehicle-photo no-photo">📷</div>
                {% endif %}
                <div class="vehicle-info">
                    <div class="vehicle-title">{{ vehicle.marca_modelo }}</div>
                    <span class="badge badge-new">Nuevo</span>
                    <div class="vehicle-details">
                        <div class="detail">
                            <span class="detail-label">Valoración</span>
                            <span class="detail-value price">{{ vehicle.valoracion|format_currency }}</span>
                        </div>
                        <div class="detail">
                            <span class="detail-label">Neto</span>
                            <span class="detail-value price">{{ vehicle.valor_neto|format_currency }}</span>
                        </div>
                        <div class="detail">
                            <span class="detail-label">Matrícula</span>
                            <span class="detail-value">{{ vehicle.matricula or 'Sin matrícula' }}</span>
                        </div>
                        <div class="detail">
                            <span class="detail-label">Fin subasta</span>
                            <span class="detail-value">{{ vehicle.fin_subasta }}</span>
                        </div>
                        <div class="detail">
                            <span class="detail-label">Tipo</span>
                            <span class="detail-value">{{ vehicle.tipo_descripcion }}</span>
                        </div>
                        <div class="detail">
                            <span class="detail-label">Combustible</span>
                            <span class="detail-value">{{ vehicle.combustible_descripcion }}</span>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div style="text-align: center; padding: 50px;">
            <h2>No hay vehículos disponibles</h2>
            <p>El scraper no ha encontrado vehículos o aún no se ha ejecutado.</p>
        </div>
        {% endif %}

        <div class="last-update">
            <p>Última actualización: {{ last_update }}</p>
        </div>
    </div>

    <script>
        function applyFilters() {
            const typeFilter = document.getElementById('typeFilter').value;
            const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
            const maxPrice = parseFloat(document.getElementById('maxPrice').value) || Infinity;

            document.querySelectorAll('.vehicle-card').forEach(card => {
                const type = card.dataset.type;
                const price = parseFloat(card.dataset.price);
                const showType = !typeFilter || type === typeFilter;
                const showPrice = price >= minPrice && price <= maxPrice;
                card.style.display = (showType && showPrice) ? 'block' : 'none';
            });
        }
    </script>
</body>
</html>
"""


class WebApp:
    """Flask web application for vehicle auction listings."""

    def __init__(
        self,
        output_dir: str = "output",
        photos_dir: str = "photos",
        host: str = "0.0.0.0",
        port: int = 5000,
    ):
        """Initialize web app.
        
        Args:
            output_dir: Directory containing vehicle data
            photos_dir: Directory containing vehicle photos
            host: Host to bind to
            port: Port to listen on
        """
        self.output_dir = Path(output_dir)
        self.photos_dir = Path(photos_dir)
        self.host = host
        self.port = port

        # Create Flask app
        self.app = Flask(__name__)
        self._register_filters()
        self._register_routes()
    
    def _register_filters(self):
        """Register Jinja2 filters."""
        @self.app.template_filter('format_currency')
        def format_currency(value):
            return f"{value:,.2f}€"

    def _register_routes(self):
        """Register Flask routes."""

        @self.app.route("/")
        def index():
            """Main page with vehicle listings."""
            # Load latest vehicle data
            vehicles = self._load_latest_vehicles()
            return render_template_string(
                HTML_TEMPLATE,
                vehicles=vehicles,
                total_valores=[v.valoracion for v in vehicles],
                tipos=list({v.tipo_descripcion for v in vehicles}),
                provincias=list({v.cod_provincia for v in vehicles}),
                last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                format_currency=lambda x: f"{x:,.2f}€",
            )

        @self.app.route("/photos/<vehicle_id>/<filename>")
        def serve_photo(vehicle_id, filename):
            """Serve vehicle photos."""
            photo_dir = self.photos_dir / vehicle_id
            return send_from_directory(photo_dir, filename)

        @self.app.route("/api/vehicles")
        def api_vehicles():
            """API endpoint for vehicle data."""
            vehicles = self._load_latest_vehicles()
            return jsonify({
                "count": len(vehicles),
                "vehicles": [v.to_dict() for v in vehicles],
            })

    def _load_latest_vehicles(self) -> list:
        """Load latest vehicle data from JSON file."""
        try:
            # Find latest JSON file
            json_files = sorted(
                self.output_dir.glob("vehiculos_*.json"),
                key=lambda x: x.name,
                reverse=True,
            )
            if not json_files:
                return []

            with open(json_files[0], "r") as f:
                data = json.load(f)

            # Convert to Vehicle objects
            from src.models.vehicle import Vehicle
            return [Vehicle(**v) for v in data]

        except Exception as e:
            logger.error("Error loading vehicles: %s", e)
            return []

    def run(self):
        """Start the web application."""
        logger.info("Starting web app on %s:%d", self.host, self.port)
        self.app.run(host=self.host, port=self.port, debug=False)
