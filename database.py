import sqlite3
import math
from pathlib import Path

DB_PATH = Path(__file__).with_name("ev_charging.db")

SAMPLE_STATIONS = [
    ("Tata Power EV Charging Station", "Patna", "Bailey Road, Patna", 25.6127, 85.1285, "DC Fast", 4, "24/7"),
    ("Ather Grid Charging Station", "Patna", "Boring Road, Patna", 25.6041, 85.1138, "Fast AC", 3, "06:00-23:00"),
    ("ChargeZone EV Station", "Patna", "Kankarbagh, Patna", 25.5942, 85.1576, "DC Fast", 6, "24/7"),
    ("Jio-bp Pulse EV Station", "Patna", "Fraser Road, Patna", 25.6090, 85.1374, "DC Fast", 5, "24/7"),
    ("Statiq EV Charging Station", "Patna", "Patliputra Colony, Patna", 25.6185, 85.0919, "AC", 2, "07:00-22:00"),
    ("Tata Power EV Charging Station", "Delhi", "Connaught Place, New Delhi", 28.6315, 77.2167, "DC Fast", 8, "24/7"),
    ("ChargeZone EV Station", "Bengaluru", "MG Road, Bengaluru", 12.9756, 77.6050, "DC Fast", 6, "24/7"),
    ("Jio-bp Pulse EV Station", "Mumbai", "Andheri East, Mumbai", 19.1197, 72.8468, "DC Fast", 5, "24/7"),
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            charger_type TEXT NOT NULL,
            connectors INTEGER NOT NULL,
            hours TEXT NOT NULL
        )
    """)
    cur.execute("SELECT COUNT(*) FROM stations")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO stations
            (name, city, address, lat, lng, charger_type, connectors, hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, SAMPLE_STATIONS)
    conn.commit()
    conn.close()

def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return 2 * r * math.asin(math.sqrt(a))

def get_stations(user_lat=None, user_lng=None, radius=50, query="", charger=""):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM stations").fetchall()
    conn.close()

    query = query.strip().lower()
    charger = charger.strip().lower()
    result = []

    for row in rows:
        if query and query not in row["name"].lower() and query not in row["city"].lower() and query not in row["address"].lower():
            continue
        if charger and charger != row["charger_type"].lower():
            continue

        item = dict(row)
        item["distance_km"] = None

        if user_lat is not None and user_lng is not None:
            item["distance_km"] = round(
                haversine(user_lat, user_lng, row["lat"], row["lng"]), 2
            )
            if item["distance_km"] > radius:
                continue

        result.append(item)

    if user_lat is not None and user_lng is not None:
        result.sort(key=lambda x: x["distance_km"])
    else:
        result.sort(key=lambda x: x["city"])

    return result
