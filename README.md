# EV Charging Finder

Complete beginner-friendly EV Charging Finder web application.

## Technology
- Python
- Flask
- SQLite
- HTML/CSS/JavaScript
- Leaflet.js
- OpenStreetMap

## Features
- Responsive UI
- Interactive map
- Sample EV charging stations
- Search by station, city or address
- Charger-type filter
- Radius filter
- Browser current-location detection
- Haversine distance calculation
- View station on map
- Google Maps navigation
- SQLite database
- No API key required

## Windows / VS Code setup

1. Open this folder in VS Code.
2. Open Terminal.
3. Run:
   `python -m venv venv`
4. Activate:
   `.\venv\Scripts\activate`
5. Install:
   `pip install -r requirements.txt`
6. Start:
   `python app.py`
7. Open:
   `http://127.0.0.1:5000`

The included stations are demo data. For production use, connect a live charging-station API.
