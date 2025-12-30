/**
 * Map Module - Leaflet map functions
 */

/**
 * Initialize the map
 */
function initMap() {
    const map = L.map('map').setView([0, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    setMap(map);
}

/**
 * Clear all markers from the map
 */
function clearMarkers() {
    const map = getMap();
    const markers = getMarkers();
    
    markers.forEach(marker => map.removeLayer(marker));
    setMarkers([]);
}

/**
 * Add scooter markers to the map with labels
 */
function addScooterMarkers(scooters) {
    clearMarkers();
    
    if (scooters.length === 0) return;
    
    const map = getMap();
    const user = getCurrentUser();
    
    scooters.forEach(scooter => {
        const isReserved = scooter.is_reserved || false;
        const iconColor = isReserved ? '#f5576c' : '#00d9ff';
        const statusText = isReserved ? '🔒' : '';
        
        // Create icon with scooter ID label
        const icon = L.divIcon({
            html: `
                <div class="scooter-marker-container">
                    <div class="scooter-marker-icon" style="background-color: ${iconColor};">
                        🛴${statusText}
                    </div>
                    <div class="scooter-marker-label" style="background-color: ${iconColor};">
                        ${scooter.id}
                    </div>
                </div>
            `,
            className: 'custom-marker-labeled',
            iconSize: [60, 50],
            iconAnchor: [30, 45]
        });
        
        const marker = L.marker([scooter.lat, scooter.lng], { icon })
            .addTo(map)
            .bindPopup(`
                <div class="popup-title">🛴 Scooter ${scooter.id}</div>
                <div class="popup-coords">📍 ${scooter.lat.toFixed(4)}, ${scooter.lng.toFixed(4)}</div>
                ${scooter.distance ? `<div class="popup-coords">📏 ${scooter.distance.toFixed(0)}m away</div>` : ''}
                <div style="margin-top: 8px;">
                    <span class="scooter-status ${isReserved ? 'status-reserved' : 'status-available'}">
                        ${isReserved ? 'Reserved' : 'Available'}
                    </span>
                </div>
                ${!isReserved && user ? `<button class="popup-btn" onclick="reserveFromMap('${scooter.id}')">Reserve This Scooter</button>` : ''}
                ${!isReserved && !user ? `<button class="popup-btn" onclick="showAuthModal()">Login to Reserve</button>` : ''}
            `);
        
        addMarker(marker);
    });
    
    // Fit bounds to show all markers
    const markers = getMarkers();
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// City locations data for map display
const MAP_CITIES = {
    'New York City': { lat: 40.7128, lng: -74.0060, region: 'US' },
    'Los Angeles': { lat: 34.0522, lng: -118.2437, region: 'US' },
    'Chicago': { lat: 41.8781, lng: -87.6298, region: 'US' },
    'Houston': { lat: 29.7604, lng: -95.3698, region: 'US' },
    'Phoenix': { lat: 33.4484, lng: -112.0740, region: 'US' },
    'San Francisco': { lat: 37.7749, lng: -122.4194, region: 'US' },
    'Seattle': { lat: 47.6062, lng: -122.3321, region: 'US' },
    'Miami': { lat: 25.7617, lng: -80.1918, region: 'US' },
    'Denver': { lat: 39.7392, lng: -104.9903, region: 'US' },
    'Austin': { lat: 30.2672, lng: -97.7431, region: 'US' },
    'London': { lat: 51.5074, lng: -0.1278, region: 'EU' },
    'Paris': { lat: 48.8566, lng: 2.3522, region: 'EU' },
    'Berlin': { lat: 52.5200, lng: 13.4050, region: 'EU' },
    'Rome': { lat: 41.9028, lng: 12.4964, region: 'EU' },
    'Amsterdam': { lat: 52.3676, lng: 4.9041, region: 'EU' },
    'Madrid': { lat: 40.4168, lng: -3.7038, region: 'EU' },
    'Tokyo': { lat: 35.6762, lng: 139.6503, region: 'APAC' },
    'Hong Kong': { lat: 22.3193, lng: 114.1694, region: 'APAC' },
    'Singapore': { lat: 1.3521, lng: 103.8198, region: 'APAC' },
    'Sydney': { lat: -33.8688, lng: 151.2093, region: 'APAC' }
};

let cityMarkersVisible = false;
let cityMarkerLayer = null;

/**
 * Toggle city markers on the map
 */
function toggleCityMarkers() {
    const map = getMap();
    
    if (cityMarkersVisible && cityMarkerLayer) {
        map.removeLayer(cityMarkerLayer);
        cityMarkersVisible = false;
        updateCityToggleButton(false);
    } else {
        addCityMarkers();
        cityMarkersVisible = true;
        updateCityToggleButton(true);
    }
}

/**
 * Update the city toggle button state
 */
function updateCityToggleButton(isActive) {
    const btn = document.getElementById('toggleCitiesBtn');
    if (btn) {
        btn.classList.toggle('active', isActive);
        btn.textContent = isActive ? '🏙️ Hide Cities' : '🏙️ Show Cities';
    }
}

/**
 * Add city markers to the map
 */
function addCityMarkers() {
    const map = getMap();
    
    // Remove existing city layer if any
    if (cityMarkerLayer) {
        map.removeLayer(cityMarkerLayer);
    }
    
    // Create a layer group for city markers
    cityMarkerLayer = L.layerGroup();
    
    Object.entries(MAP_CITIES).forEach(([cityName, city]) => {
        const regionColors = {
            'US': '#4facfe',
            'EU': '#f093fb',
            'APAC': '#43e97b'
        };
        const color = regionColors[city.region] || '#888';
        
        const cityIcon = L.divIcon({
            html: `
                <div class="city-marker-container">
                    <div class="city-marker-pin" style="background: ${color};">
                        🏙️
                    </div>
                    <div class="city-marker-label" style="border-color: ${color};">
                        ${cityName}
                    </div>
                </div>
            `,
            className: 'city-marker',
            iconSize: [100, 45],
            iconAnchor: [50, 40]
        });
        
        const cityMarker = L.marker([city.lat, city.lng], { icon: cityIcon })
            .bindPopup(`
                <div class="popup-title">🏙️ ${cityName}</div>
                <div class="popup-coords">📍 ${city.lat.toFixed(4)}, ${city.lng.toFixed(4)}</div>
                <div class="popup-region">Region: ${city.region === 'US' ? '🇺🇸 United States' : city.region === 'EU' ? '🇪🇺 Europe' : '🌏 Asia Pacific'}</div>
            `);
        
        cityMarkerLayer.addLayer(cityMarker);
    });
    
    cityMarkerLayer.addTo(map);
}

/**
 * Add user location marker
 */
function addUserLocationMarker(lat, lng) {
    const map = getMap();
    
    const userIcon = L.divIcon({
        html: `<div style="
            background: linear-gradient(135deg, #00c851, #007e33);
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 4px solid white;
            box-shadow: 0 0 20px rgba(0, 200, 81, 0.6), 0 3px 10px rgba(0,0,0,0.4);
        "></div>`,
        className: 'user-location-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
    
    const userMarker = L.marker([lat, lng], { icon: userIcon })
        .addTo(map)
        .bindPopup('<div class="popup-title">📍 Your Location</div>');
    
    addMarker(userMarker);
}

/**
 * Add search location marker
 */
function addSearchLocationMarker(lat, lng, name) {
    const map = getMap();
    
    const locationIcon = L.divIcon({
        html: `<div style="
            background: linear-gradient(135deg, #f093fb, #f5576c);
            width: 28px;
            height: 28px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 3px 15px rgba(240, 147, 251, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        ">📍</div>`,
        className: 'location-marker',
        iconSize: [28, 28],
        iconAnchor: [14, 14]
    });
    
    const locationMarker = L.marker([lat, lng], { icon: locationIcon })
        .addTo(map)
        .bindPopup(`<div class="popup-title">📍 ${name}</div>`);
    
    addMarker(locationMarker);
}

/**
 * Add search radius circle to map
 */
function addSearchRadiusCircle(lat, lng, radius) {
    const map = getMap();
    
    const circle = L.circle([lat, lng], {
        radius: radius,
        color: '#00c851',
        fillColor: '#00c851',
        fillOpacity: 0.1,
        weight: 2
    }).addTo(map);
    
    addMarker(circle);
}

/**
 * Focus map on a location
 */
function focusScooter(lat, lng) {
    getMap().setView([lat, lng], 15);
}

/**
 * Enable click-on-map search
 */
function enableMapClickSearch() {
    getMap().on('click', onMapClick);
}

/**
 * Handle map click for search
 */
function onMapClick(e) {
    const map = getMap();
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    
    // Remove previous click marker
    const prevMarker = getClickSearchMarker();
    if (prevMarker) {
        map.removeLayer(prevMarker);
    }
    
    const clickIcon = L.divIcon({
        html: `<div style="
            background: linear-gradient(135deg, #4facfe, #00f2fe);
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 3px 10px rgba(0,0,0,0.4);
            cursor: pointer;
        "></div>`,
        className: 'click-search-marker',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
    
    const clickMarker = L.marker([lat, lng], { icon: clickIcon })
        .addTo(map)
        .bindPopup(`
            <div class="click-search-popup">
                <h4>🔍 Search Here</h4>
                <div class="popup-coords">📍 ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
                <select class="click-search-radius-select" id="clickRadius">
                    <option value="500">500m radius</option>
                    <option value="1000" selected>1km radius</option>
                    <option value="2000">2km radius</option>
                    <option value="5000">5km radius</option>
                </select>
                <button class="popup-btn" onclick="searchFromMapClick(${lat}, ${lng})">
                    Find Scooters Here
                </button>
            </div>
        `, { closeButton: true })
        .openPopup();
    
    setClickSearchMarker(clickMarker);
}

