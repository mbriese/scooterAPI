// API Base URL
const API_BASE = window.location.origin;

// Initialize map
let map;
let markers = [];

// Initialize Leaflet map
function initMap() {
    map = L.map('map').setView([0, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
}

// Clear all markers from map
function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

// Add scooter markers to map
function addScooterMarkers(scooters) {
    clearMarkers();
    
    if (scooters.length === 0) {
        return;
    }
    
    scooters.forEach(scooter => {
        const isReserved = scooter.is_reserved || false;
        const iconColor = isReserved ? 'red' : 'blue';
        
        const icon = L.divIcon({
            html: `<div style="background-color: ${iconColor}; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">🛴</div>`,
            className: 'custom-marker',
            iconSize: [30, 30]
        });
        
        const marker = L.marker([scooter.lat, scooter.lng], { icon: icon })
            .addTo(map)
            .bindPopup(`
                <div class="popup-title">Scooter ${scooter.id}</div>
                <div class="popup-coords">📍 ${scooter.lat.toFixed(4)}, ${scooter.lng.toFixed(4)}</div>
                <div style="margin-top: 8px;">
                    <span class="scooter-status ${isReserved ? 'status-reserved' : 'status-available'}">
                        ${isReserved ? 'Reserved' : 'Available'}
                    </span>
                </div>
                ${!isReserved ? `<button class="popup-btn" onclick="reserveFromMap('${scooter.id}')">Reserve This Scooter</button>` : ''}
            `);
        
        markers.push(marker);
    });
    
    // Fit map to show all markers
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Show status message
function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type} show`;
    
    setTimeout(() => {
        statusDiv.classList.remove('show');
    }, 5000);
}

// View all available scooters
async function viewAllScooters() {
    try {
        showStatus('Loading available scooters...', 'info');
        
        const response = await fetch(`${API_BASE}/view_all_available`);
        const data = await response.json();
        
        if (response.ok) {
            displayScooterList(data);
            addScooterMarkers(data);
            showStatus(`Found ${data.length} available scooters`, 'success');
        } else {
            showStatus(data.msg || 'Failed to load scooters', 'error');
        }
    } catch (error) {
        showStatus('Error connecting to API: ' + error.message, 'error');
    }
}

// Display scooter list
function displayScooterList(scooters) {
    const listDiv = document.getElementById('scooterList');
    
    if (scooters.length === 0) {
        listDiv.innerHTML = '<div class="empty-state">No scooters available</div>';
        return;
    }
    
    listDiv.innerHTML = scooters.map(scooter => `
        <div class="scooter-item" onclick="focusScooter(${scooter.lat}, ${scooter.lng})">
            <div class="scooter-info">
                <div class="scooter-id">🛴 Scooter ${scooter.id}</div>
                <div class="scooter-coords">📍 ${scooter.lat.toFixed(4)}, ${scooter.lng.toFixed(4)}</div>
            </div>
            <span class="scooter-status ${scooter.is_reserved ? 'status-reserved' : 'status-available'}">
                ${scooter.is_reserved ? 'Reserved' : 'Available'}
            </span>
        </div>
    `).join('');
}

// Focus map on specific scooter
function focusScooter(lat, lng) {
    map.setView([lat, lng], 15);
}

// Search for scooters
async function searchScooters(lat, lng, radius) {
    try {
        showStatus('Searching for scooters...', 'info');
        
        const response = await fetch(`${API_BASE}/search?lat=${lat}&lng=${lng}&radius=${radius}`);
        const data = await response.json();
        
        if (response.ok) {
            addScooterMarkers(data);
            
            // Add search location marker
            const searchIcon = L.divIcon({
                html: '<div style="background-color: green; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>',
                className: 'search-marker',
                iconSize: [20, 20]
            });
            const searchMarker = L.marker([lat, lng], { icon: searchIcon })
                .addTo(map)
                .bindPopup('📍 Search Location');
            markers.push(searchMarker);
            
            // Draw search radius circle
            const circle = L.circle([lat, lng], {
                radius: radius,
                color: 'green',
                fillColor: '#30ff30',
                fillOpacity: 0.1
            }).addTo(map);
            markers.push(circle);
            
            map.setView([lat, lng], 13);
            
            showStatus(`Found ${data.length} scooters within ${radius}m`, 'success');
            
            // Display results in list
            displayScooterList(data);
        } else {
            showStatus(data.msg || 'Search failed', 'error');
        }
    } catch (error) {
        showStatus('Error searching: ' + error.message, 'error');
    }
}

// Reserve a scooter
async function reserveScooter(scooterId) {
    try {
        showStatus(`Reserving scooter ${scooterId}...`, 'info');
        
        const response = await fetch(`${API_BASE}/reservation/start?id=${scooterId}`);
        const data = await response.json();
        
        if (response.ok) {
            showStatus(data.msg, 'success');
            // Refresh the list
            viewAllScooters();
        } else {
            showStatus(data.msg || 'Reservation failed', 'error');
        }
    } catch (error) {
        showStatus('Error reserving: ' + error.message, 'error');
    }
}

// Reserve from map popup
function reserveFromMap(scooterId) {
    document.getElementById('reserveId').value = scooterId;
    document.getElementById('reserveForm').scrollIntoView({ behavior: 'smooth' });
    reserveScooter(scooterId);
}

// End reservation
async function endReservation(scooterId, lat, lng) {
    try {
        showStatus(`Ending reservation for scooter ${scooterId}...`, 'info');
        
        const response = await fetch(`${API_BASE}/reservation/end?id=${scooterId}&lat=${lat}&lng=${lng}`);
        const data = await response.json();
        
        if (response.ok) {
            showStatus(`${data.msg} (Transaction ID: ${data.txn_id})`, 'success');
            // Refresh the list
            viewAllScooters();
        } else {
            showStatus(data.msg || 'Failed to end reservation', 'error');
        }
    } catch (error) {
        showStatus('Error ending reservation: ' + error.message, 'error');
    }
}

// Get user's current location
function getUserLocation(callback) {
    if (navigator.geolocation) {
        showStatus('Getting your location...', 'info');
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                callback(lat, lng);
                showStatus('Location acquired!', 'success');
            },
            (error) => {
                showStatus('Unable to get your location: ' + error.message, 'error');
            }
        );
    } else {
        showStatus('Geolocation is not supported by your browser', 'error');
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize map
    initMap();
    
    // Load all scooters on page load
    viewAllScooters();
    
    // View All button
    document.getElementById('viewAllBtn').addEventListener('click', viewAllScooters);
    
    // Search form
    document.getElementById('searchForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const lat = parseFloat(document.getElementById('searchLat').value);
        const lng = parseFloat(document.getElementById('searchLng').value);
        const radius = parseInt(document.getElementById('searchRadius').value);
        searchScooters(lat, lng, radius);
    });
    
    // Use location button for search
    document.getElementById('useLocationBtn').addEventListener('click', () => {
        getUserLocation((lat, lng) => {
            document.getElementById('searchLat').value = lat.toFixed(6);
            document.getElementById('searchLng').value = lng.toFixed(6);
            map.setView([lat, lng], 13);
        });
    });
    
    // Reserve form
    document.getElementById('reserveForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const scooterId = document.getElementById('reserveId').value;
        reserveScooter(scooterId);
    });
    
    // End reservation form
    document.getElementById('endForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const scooterId = document.getElementById('endId').value;
        const lat = parseFloat(document.getElementById('endLat').value);
        const lng = parseFloat(document.getElementById('endLng').value);
        endReservation(scooterId, lat, lng);
    });
    
    // Use location button for end reservation
    document.getElementById('useEndLocationBtn').addEventListener('click', () => {
        getUserLocation((lat, lng) => {
            document.getElementById('endLat').value = lat.toFixed(6);
            document.getElementById('endLng').value = lng.toFixed(6);
        });
    });
});



