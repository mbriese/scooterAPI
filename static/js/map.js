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
 * Add scooter markers to the map
 */
function addScooterMarkers(scooters) {
    clearMarkers();
    
    if (scooters.length === 0) return;
    
    const map = getMap();
    const user = getCurrentUser();
    
    scooters.forEach(scooter => {
        const isReserved = scooter.is_reserved || false;
        const iconColor = isReserved ? '#f5576c' : '#00d9ff';
        
        const icon = L.divIcon({
            html: `<div style="background-color: ${iconColor}; width: 32px; height: 32px; border-radius: 50%; border: 3px solid white; box-shadow: 0 3px 10px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; font-size: 16px;">🛴</div>`,
            className: 'custom-marker',
            iconSize: [32, 32]
        });
        
        const marker = L.marker([scooter.lat, scooter.lng], { icon })
            .addTo(map)
            .bindPopup(`
                <div class="popup-title">Scooter ${scooter.id}</div>
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

