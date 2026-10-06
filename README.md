# EV Charging Finder — Live API Edition

A Flask + Leaflet EV charging finder with **live nearby EV-station data** from Google Places API (New).

## What changed

- Replaced the old hard-coded station database with a live API adapter.
- Uses `electric_vehicle_charging_station` Nearby Search.
- Shows station name, address, coordinates, connector count and connector types when supplied.
- Shows reported available connector count and the provider's availability update timestamp when supplied.
- Keeps current-location detection and Google Maps navigation.
- Radius is limited to Google's Nearby Search maximum of 50 km.
- Includes a safe demo fallback when no API key is configured.
- Render-ready `render.yaml` and production Gunicorn start command included.

> Important: "real-time" availability depends on whether the station/operator data provider reports current connector availability. A station can have live location/details without live occupied/free status.

## 1. Create a Google Maps Platform API key

1. Create/select a Google Cloud project.
2. Enable **Places API (New)**.
3. Create an API key.
4. Restrict the key to the APIs/services you actually use. Do not put the key directly in source code.
5. Make sure the required Google Maps Platform billing setup is enabled for your account.

The application calls:
`https://places.googleapis.com/v1/places:searchNearby`

## 2. Run locally

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
$env:GOOGLE_MAPS_API_KEY="YOUR_KEY_HERE"
python app.py
```

Then open `http://127.0.0.1:5000`.

For Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GOOGLE_MAPS_API_KEY="YOUR_KEY_HERE"
python app.py
```

If the API key is missing, the app displays one demo station instead of crashing.

## 3. Deploy/update on Render

### Option A — Existing Render service connected to GitHub

1. Replace the old project files with this project.
2. Commit and push to the branch connected to Render.
3. Render automatically builds/deploys the new commit.
4. In Render Dashboard → your service → **Environment**, add:
   - Key: `GOOGLE_MAPS_API_KEY`
   - Value: your Google API key
5. Choose **Save, rebuild, and deploy**.

Build command:
`pip install -r requirements.txt`

Start command:
`gunicorn app:app`

### Option B — Render Blueprint

The included `render.yaml` declares the web service, free plan, build/start commands, Python version, and a secret environment variable placeholder. After connecting the repository, provide the API key in Render rather than committing it to Git.

## 4. How the live flow works

Browser location → Flask `/api/stations` → Google Places Nearby Search → live station data → Leaflet map/list.

When the user has not granted location, the first view searches around the app's default Patna location. Clicking **Use My Location** refreshes the live results around the user's actual browser location.

## 5. Files

```text
EV_Charging_Finder_Live
├── app.py
├── database.py
├── requirements.txt
├── render.yaml
├── .env.example
├── README.md
├── templates
│   └── index.html
└── static
    ├── app.js
    └── style.css
```

## Notes

- The Google API key stays on the server; it is never sent to browser JavaScript.
- Do not commit a real API key to GitHub.
- Google Places API field selection affects billing, so this project requests only the fields it needs for the station cards and availability information.
