import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Aapki Open Charge Map API Key
OCM_API_KEY = "45900e0c-04e6-4f82-abe2-13dbc8187858"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stations")
def stations_api():
    # Agar user location na mile toh default Bihar/Patna coordinates
    lat = request.args.get("lat", default=25.6127, type=float)
    lng = request.args.get("lng", default=85.1285, type=float)
    radius = request.args.get("radius", default=50, type=float)
    query = request.args.get("q", default="", type=str).strip().lower()
    charger = request.args.get("charger", default="", type=str).strip().lower()

    url = "https://api.openchargemap.io/v3/poi/"
    headers = {
        "X-API-Key": OCM_API_KEY,
        "User-Agent": "EVChargingFinderApp/1.0"
    }
    params = {
        "output": "json",
        "latitude": lat,
        "longitude": lng,
        "distance": radius,
        "distanceunit": "KM",
        "maxresults": 50,
        "compact": "true",
        "verbose": "false"
    }

    stations = []
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                addr = item.get("AddressInfo", {})
                title = addr.get("Title", "EV Station")
                town = addr.get("Town", "")
                address_line = addr.get("AddressLine1", "") or f"{town}, India"

                # Search filter
                if query and (query not in title.lower() and query not in address_line.lower() and query not in town.lower()):
                    continue

                # Connections / Charger type calculate karein
                connections = item.get("Connections", [])
                charger_types = []
                for conn in connections:
                    conn_type = conn.get("ConnectionType", {}).get("Title", "")
                    if conn_type:
                        charger_types.append(conn_type)
                charger_str = ", ".join(charger_types[:2]) if charger_types else "Fast / AC"

                if charger and charger not in charger_str.lower():
                    continue

                dist = addr.get("Distance")
                stations.append({
                    "name": title,
                    "city": town,
                    "address": address_line,
                    "lat": addr.get("Latitude"),
                    "lng": addr.get("Longitude"),
                    "charger_type": charger_str,
                    "connectors": len(connections) if connections else 1,
                    "hours": "24/7",
                    "distance_km": round(dist, 2) if dist is not None else None
                })
        else:
            print(f"OCM Error: {response.status_code}")
    except Exception as err:
        print("API Fetch Exception:", err)

    # Kabhi bhi 400 error return nahi karega, hamesha valid JSON bhejega
    return jsonify(stations)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
