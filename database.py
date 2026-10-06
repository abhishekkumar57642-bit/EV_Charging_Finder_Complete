"""Live EV charging-station data adapter.

The app uses Google Places API (New) when GOOGLE_MAPS_API_KEY is configured.
A small demo fallback is kept for local development when no key is present.
"""
import math
import os
from pathlib import Path

import requests

DB_PATH = Path(__file__).with_name("ev_charging.db")
GOOGLE_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"

DEMO_STATIONS = [
    {"name": "Demo EV Charging Station", "city": "Patna", "address": "Patna, Bihar", "lat": 25.6127, "lng": 85.1285,
     "charger_type": "DC Fast", "connectors": 4, "available_connectors": None, "hours": "24/7", "status": "Demo data", "source": "demo"}
]


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _connector_label(connector_type, rate_kw):
    connector_type = (connector_type or "").replace("EV_CONNECTOR_TYPE_", "").replace("_", " ").title()
    if rate_kw is not None:
        try:
            rate = float(rate_kw)
            if rate >= 50:
                return f"DC Fast ({rate:g} kW)"
            if rate > 7:
                return f"Fast ({rate:g} kW)"
            return f"AC ({rate:g} kW)"
        except (TypeError, ValueError):
            pass
    return connector_type or "EV Charger"


def _normalise_place(place, user_lat, user_lng):
    location = place.get("location") or {}
    lat = location.get("latitude")
    lng = location.get("longitude")
    if lat is None or lng is None:
        return None

    ev = place.get("evChargeOptions") or {}
    aggregations = ev.get("connectorAggregation") or []
    connector_count = ev.get("connectorCount")
    if connector_count is None:
        connector_count = sum(int(a.get("count", 0) or 0) for a in aggregations)

    available = sum(int(a.get("availableCount", 0) or 0) for a in aggregations if "availableCount" in a)
    has_availability = any("availableCount" in a for a in aggregations)
    rates = [a.get("maxChargeRateKw") for a in aggregations if a.get("maxChargeRateKw") is not None]
    max_rate = max([float(x) for x in rates], default=None)
    types = [_connector_label(a.get("type"), a.get("maxChargeRateKw")) for a in aggregations]
    charger_type = types[0] if types else ("DC Fast" if (max_rate or 0) >= 50 else "EV Charger")

    status = place.get("businessStatus", "UNKNOWN").replace("_", " ").title()
    if has_availability:
        if available > 0:
            status = f"{available} connector(s) available"
        else:
            status = "No connector availability reported"

    distance = round(haversine(user_lat, user_lng, lat, lng), 2) if user_lat is not None and user_lng is not None else None
    address = place.get("shortFormattedAddress") or place.get("formattedAddress") or "Address unavailable"
    city = address.split(",")[-2].strip() if "," in address and len(address.split(",")) >= 2 else ""

    last_update = None
    for agg in aggregations:
        if agg.get("availabilityLastUpdateTime"):
            last_update = agg["availabilityLastUpdateTime"]
            break

    return {
        "id": place.get("id"),
        "name": (place.get("displayName") or {}).get("text", "EV Charging Station"),
        "city": city,
        "address": address,
        "lat": lat,
        "lng": lng,
        "charger_type": charger_type,
        "connector_types": types,
        "connectors": connector_count,
        "available_connectors": available if has_availability else None,
        "max_charge_rate_kw": max_rate,
        "hours": "See station details",
        "status": status,
        "business_status": place.get("businessStatus", "UNKNOWN"),
        "last_updated": last_update,
        "google_maps_uri": place.get("googleMapsUri"),
        "website_uri": place.get("websiteUri"),
        "distance_km": distance,
        "source": "Google Places API (New)",
    }


def get_stations(user_lat=None, user_lng=None, radius=50, query="", charger=""):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        return _filter_demo(user_lat, user_lng, radius, query, charger)
    if user_lat is None or user_lng is None:
        return {"error": "location_required", "message": "Use My Location to load live nearby charging stations."}

    # Google Nearby Search supports a maximum radius of 50 km and 20 results.
    radius_km = min(max(float(radius or 50), 0.1), 50.0)
    body = {
        "includedTypes": ["electric_vehicle_charging_station"],
        "maxResultCount": 20,
        "rankPreference": "DISTANCE",
        "regionCode": "IN",
        "languageCode": "en",
        "locationRestriction": {
            "circle": {
                "center": {"latitude": user_lat, "longitude": user_lng},
                "radius": radius_km * 1000,
            }
        },
    }
    field_mask = ",".join([
        "places.id", "places.displayName", "places.location", "places.shortFormattedAddress",
        "places.formattedAddress", "places.businessStatus", "places.googleMapsUri", "places.websiteUri",
        "places.evChargeOptions"
    ])

    try:
        response = requests.post(
            GOOGLE_NEARBY_URL,
            json=body,
            headers={"Content-Type": "application/json", "X-Goog-Api-Key": api_key, "X-Goog-FieldMask": field_mask},
            timeout=12,
        )
        if not response.ok:
            try:
                detail = response.json().get("error", {}).get("message", response.text)
            except ValueError:
                detail = response.text
            return {"error": "provider_error", "message": f"Live station provider error: {detail}"}
        data = response.json()
    except requests.RequestException as exc:
        return {"error": "network_error", "message": f"Could not reach live station provider: {exc}"}

    results = []
    query_l = query.strip().lower()
    charger_l = charger.strip().lower()
    for place in data.get("places", []):
        item = _normalise_place(place, user_lat, user_lng)
        if not item:
            continue
        searchable = " ".join([
            item["name"], item["city"], item["address"], " ".join(item.get("connector_types", [])), item["charger_type"]
        ]).lower()
        if query_l and query_l not in searchable:
            continue
        if charger_l:
            connector_text = " ".join(item.get("connector_types", [])).lower()
            if charger_l not in connector_text and charger_l not in item["charger_type"].lower():
                continue
        results.append(item)

    results.sort(key=lambda x: x["distance_km"] if x["distance_km"] is not None else 999999)
    return {"stations": results, "live": True, "provider": "Google Places API (New)"}


def _filter_demo(user_lat, user_lng, radius, query, charger):
    query_l = query.strip().lower()
    charger_l = charger.strip().lower()
    result = []
    for item in DEMO_STATIONS:
        if query_l and query_l not in (item["name"] + item["city"] + item["address"]).lower():
            continue
        if charger_l and charger_l not in item["charger_type"].lower():
            continue
        item = dict(item)
        item["distance_km"] = None
        if user_lat is not None and user_lng is not None:
            item["distance_km"] = round(haversine(user_lat, user_lng, item["lat"], item["lng"]), 2)
            if item["distance_km"] > float(radius or 50):
                continue
        result.append(item)
    return {"stations": result, "live": False, "provider": "Demo data", "message": "Add GOOGLE_MAPS_API_KEY on Render for live data."}
