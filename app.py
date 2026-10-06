 import requests
    from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
OCM_API_KEY = "45900e0c-04e6-4f82-abe2-13dbc8187858"
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stations")
def stations_api():
    # .get() use karein taaki parameter missing hone par 400 na aaye
    lat = request.args.get("lat", default=25.6127, type=float)
    lng = request.args.get("lng", default=85.1285, type=float)
    radius = request.args.get("radius", default=50, type=float)
    query = request.args.get("q", default="", type=str).strip().lower()

    # Open Charge Map API endpoint
    url = "https://api.openchargemap.io/v3/poi/"
    headers = {
        "X-API-Key": OCM_API_KEY,
        "User-Agent": "EVChargingFinder/1.0"  # OCM ke liye zaroori hai
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
        res = requests.get(url, headers=headers, params=params, timeout=10)
        
        # Agar OCM error de raha ho toh crash hone se bachayein
        if res.status_code == 200:
            raw_data = res.json()
            for item in raw_data:
                addr = item.get("AddressInfo", {})
                title = addr.get("Title", "EV Station")
                city = addr.get("Town", "")
                address = addr.get("AddressLine1", "") or f"{city}, India"
                
                # Search filter
                if query and (query not in title.lower() and query not in address.lower()):
                    continue

                distance = addr.get("Distance")
                stations.append({
                    "name": title,
                    "city": city,
                    "address": address,
                    "lat": addr.get("Latitude"),
                    "lng": addr.get("Longitude"),
                    "charger_type": "Fast / AC",
                    "connectors": len(item.get("Connections", [])) or 1,
                    "hours": "24/7",
                    "distance_km": round(distance, 2) if distance else None
                })
        else:
            print("OCM API Error Status:", res.status_code, res.text)
    except Exception as e:
        print("Backend Fetch Exception:", e)

    return jsonify(stations)

if _name_ == "_main_":
    app.run(debug=True, host="0.0.0.0", port=5000)
