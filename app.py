from flask import Flask, render_template, jsonify, request
from database import get_stations

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stations")
def stations_api():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius = request.args.get("radius", default=25, type=float)
    query = request.args.get("q", default="", type=str)
    charger = request.args.get("charger", default="", type=str)
    result = get_stations(lat, lng, radius, query, charger)
    if isinstance(result, dict) and result.get("error"):
        return jsonify(result), 400
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
