let map;
let markers = [];
let userMarker = null;
let userLocation = null;
const defaultCenter = [25.6127, 85.1285];

document.addEventListener("DOMContentLoaded", () => {
    map = L.map("map").setView(defaultCenter, 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom:19,
        attribution:'&copy; OpenStreetMap contributors'
    }).addTo(map);

    loadStations();
    document.getElementById("searchBtn").addEventListener("click", loadStations);
    document.getElementById("locationBtn").addEventListener("click", locateUser);
    document.getElementById("searchInput").addEventListener("keydown", e => {
        if (e.key === "Enter") loadStations();
    });
    document.getElementById("chargerFilter").addEventListener("change", loadStations);
    document.getElementById("radiusFilter").addEventListener("change", loadStations);
});

async function loadStations() {
    const q = document.getElementById("searchInput").value.trim();
    const charger = document.getElementById("chargerFilter").value;
    const radius = document.getElementById("radiusFilter").value;
    const params = new URLSearchParams({q, charger, radius});

    if (userLocation) {
        params.set("lat", userLocation.lat);
        params.set("lng", userLocation.lng);
    }

    setStatus("Loading charging stations...");

    try {
        const response = await fetch(`/api/stations?${params.toString()}`);
        if (!response.ok) throw new Error("Server error");
        displayStations(await response.json());
    } catch (error) {
        setStatus("Could not load stations. Check that Flask is running.");
        console.error(error);
    }
}

function displayStations(stations) {
    clearMarkers();
    const list = document.getElementById("stationList");
    document.getElementById("count").textContent = stations.length;

    if (!stations.length) {
        list.innerHTML = '<div class="empty">No charging stations found.</div>';
        return;
    }

    list.innerHTML = "";
    const bounds = [];

    stations.forEach(station => {
        const marker = L.marker([station.lat, station.lng]).addTo(map);
        const distance = station.distance_km !== null
            ? `<strong>${station.distance_km} km away</strong>`
            : "Distance unavailable";

        marker.bindPopup(`
            <b>${escapeHtml(station.name)}</b><br>
            ${escapeHtml(station.address)}<br>
            ${escapeHtml(station.charger_type)} · ${station.connectors} connectors
        `);

        markers.push(marker);
        bounds.push([station.lat, station.lng]);

        const navUrl = `https://www.google.com/maps/dir/?api=1&destination=${station.lat},${station.lng}`;
        const card = document.createElement("div");
        card.className = "station";
        card.innerHTML = `
            <h3>⚡ ${escapeHtml(station.name)}</h3>
            <p>📍 ${escapeHtml(station.address)}</p>
            <p>🕒 ${escapeHtml(station.hours)}</p>
            <p>📏 ${distance}</p>
            <span class="badge">${escapeHtml(station.charger_type)}</span>
            <span class="badge">${station.connectors} connectors</span>
            <div class="station-actions">
                <button class="small-btn view-btn">View on Map</button>
                <a class="small-btn" href="${navUrl}" target="_blank" rel="noopener">Navigate</a>
            </div>
        `;

        card.querySelector(".view-btn").addEventListener("click", () => {
            map.setView([station.lat, station.lng], 16);
            marker.openPopup();
        });
        list.appendChild(card);
    });

    if (userLocation) bounds.push([userLocation.lat, userLocation.lng]);
    if (bounds.length > 1) map.fitBounds(bounds, {padding:[30,30]});
    else if (bounds.length === 1) map.setView(bounds[0], 14);

    setStatus(userLocation
        ? `Found ${stations.length} station(s) near your location.`
        : `Found ${stations.length} charging station(s).`);
}

function locateUser() {
    if (!navigator.geolocation) {
        setStatus("Your browser does not support location detection.");
        return;
    }

    setStatus("Requesting your location...");

    navigator.geolocation.getCurrentPosition(
        position => {
            userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };

            if (userMarker) map.removeLayer(userMarker);
            userMarker = L.marker([userLocation.lat, userLocation.lng])
                .addTo(map).bindPopup("📍 You are here");

            map.setView([userLocation.lat, userLocation.lng], 13);
            userMarker.openPopup();
            loadStations();
        },
        error => {
            let message = "Could not get your location.";
            if (error.code === 1) {
                message = "Location permission was denied. Please allow location access.";
            }
            setStatus(message);
        },
        {enableHighAccuracy:true, timeout:10000, maximumAge:60000}
    );
}

function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

function setStatus(message) {
    document.getElementById("status").textContent = message;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}
