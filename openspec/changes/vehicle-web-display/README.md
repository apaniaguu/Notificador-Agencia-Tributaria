# Vehicle Web Display

## Descripción
Especificación OpenSpec para la página web de visualización de vehículos de la Agencia Tributaria.

## Objetivo
Crear una aplicación web sencilla que muestre los vehículos disponibles en las subastas de la AEAT con imágenes y toda la información relevante.

## Estado
- **Especificación**: ✅ Creada
- **Implementación**: ✅ Completada
- **Tests**: ✅ 37 tests pasando

## Componentes Implementados

### 1. Frontend (Flask + HTML Template)
- **Ruta**: `/`
- **Funcionalidad**: Muestra lista de vehículos con fotos y detalles
- **Tecnología**: Flask con templates HTML y CSS inline

### 2. Estadísticas
- **Ruta**: `/stats`
- **Funcionalidad**: Muestra totales de scrapes y vehículos
- **Tecnología**: Flask con datos de la base de datos

### 3. Logs
- **Ruta**: `/logs`
- **Funcionalidad**: Muestra logs de notificaciones de Telegram
- **Tecnología**: Flask con fetch a API

## Estructura de Datos

### Vista Principal
Cada vehículo muestra:
- Marca y modelo
- Hasta 5 fotos en grid responsive
- Valoración, cargas y valor neto (€)
- Fecha fin de subasta
- Tipo de vehículo
- Matrícula
- Código provincia

### Responsive
- Desktop (>768px): 5 columnas de fotos, 4 columnas de info
- Mobile (<768px): 3 columnas de fotos, 1 columna de info

## Instalación

```bash
cd /home/apaniaguu/Notificador-Agencia-Tributaria
source venv/bin/activate

# Instalar Flask
pip install flask

# Ejecutar
python src/webapp/app.py
```

## Uso

```bash
# Iniciar servidor
python src/webapp/app.py

# Acceder
curl http://localhost:5001/
curl http://localhost:5001/stats
curl http://localhost:5001/logs
```

## Dependencias

- Flask
- SQLAlchemy
- OpenSpec CLI
- Scrapers AEAT
- Telegram bot

## Tests

```bash
pytest tests/
```

## Próximos Pasos

- Agregar paginación para muchos vehículos
- Añadir filtros de búsqueda
- Implementar autenticación opcional
- Agregar exportar a PDF
- Agregar modo oscuro

## Notas de Implementación

- El scraping se realiza en tiempo real al cargar la página
- Las fotos se muestran como URLs directas
- El layout es responsive por defecto
- Se usa la base de datos existente para historial
