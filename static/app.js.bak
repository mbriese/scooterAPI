// API Base URL
const API_BASE = window.location.origin;
const NOMINATIM_API = 'https://nominatim.openstreetmap.org';

// App State
let currentUser = null;
let map;
let markers = [];
let searchRadius = 1000; // Default 1km
let addressSearchTimeout = null;
let clickSearchMarker = null;

// ==================
// AUTHENTICATION
// ==================

// Check if user is logged in on page load
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            updateUIForLoggedInUser();
        } else {
            currentUser = null;
            updateUIForLoggedOutUser();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        currentUser = null;
        updateUIForLoggedOutUser();
    }
}

// Login
async function login(email, password) {
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            hideAuthModal();
            updateUIForLoggedInUser();
            showStatus(`Welcome back, ${currentUser.name}!`, 'success');
            return { success: true };
        } else {
            return { success: false, error: data.msg };
        }
    } catch (error) {
        return { success: false, error: 'Connection error. Please try again.' };
    }
}

// Register
async function register(name, email, password) {
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            hideAuthModal();
            updateUIForLoggedInUser();
            showStatus(`Welcome, ${currentUser.name}! Your account has been created.`, 'success');
            return { success: true };
        } else {
            return { success: false, error: data.msg };
        }
    } catch (error) {
        return { success: false, error: 'Connection error. Please try again.' };
    }
}

// Logout
async function logout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    currentUser = null;
    updateUIForLoggedOutUser();
    showStatus('You have been logged out.', 'info');
}

// ==================
// UI UPDATES
// ==================

function updateUIForLoggedInUser() {
    // Hide login button, show user info
    document.getElementById('showLoginBtn').classList.add('hidden');
    document.getElementById('userInfo').classList.remove('hidden');
    
    // Update user info display
    document.getElementById('userName').textContent = currentUser.name;
    const roleSpan = document.getElementById('userRole');
    roleSpan.textContent = currentUser.role;
    roleSpan.className = `user-role ${currentUser.role}`;
    
    // Show renter features
    document.querySelectorAll('.renter-feature').forEach(el => {
        el.querySelector('.login-prompt')?.classList.add('hidden');
        el.querySelector('form')?.classList.remove('hidden');
    });
    
    // Show/hide admin panel
    if (currentUser.role === 'admin') {
        document.getElementById('adminPanel').classList.remove('hidden');
        loadAdminData();
    } else {
        document.getElementById('adminPanel').classList.add('hidden');
    }
}

function updateUIForLoggedOutUser() {
    // Show login button, hide user info
    document.getElementById('showLoginBtn').classList.remove('hidden');
    document.getElementById('userInfo').classList.add('hidden');
    
    // Hide admin panel
    document.getElementById('adminPanel').classList.add('hidden');
    
    // Show login prompts for renter features
    document.querySelectorAll('.renter-feature').forEach(el => {
        el.querySelector('.login-prompt')?.classList.remove('hidden');
        el.querySelector('form')?.classList.add('hidden');
    });
}

function showAuthModal() {
    document.getElementById('authModal').classList.add('show');
}

function hideAuthModal() {
    document.getElementById('authModal').classList.remove('show');
    // Clear forms
    document.getElementById('loginForm').reset();
    document.getElementById('registerForm').reset();
    document.getElementById('loginError').classList.remove('show');
    document.getElementById('registerError').classList.remove('show');
}

// ==================
// ADMIN FUNCTIONS
// ==================

async function loadAdminData() {
    await loadUsers();
    await loadFleet();
}

async function loadUsers() {
    const listDiv = document.getElementById('usersList');
    listDiv.innerHTML = '<div class="loading-text">Loading users...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/admin/users`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            displayUsers(data.users);
        } else {
            listDiv.innerHTML = '<div class="empty-state">Failed to load users</div>';
        }
    } catch (error) {
        listDiv.innerHTML = '<div class="empty-state">Error loading users</div>';
    }
}

function displayUsers(users) {
    const listDiv = document.getElementById('usersList');
    
    if (!users || users.length === 0) {
        listDiv.innerHTML = '<div class="empty-state">No users found</div>';
        return;
    }
    
    listDiv.innerHTML = users.map(user => `
        <div class="user-item">
            <div class="user-details">
                <div class="user-email">${user.name}</div>
                <div class="user-meta">${user.email} • Joined ${new Date(user.created_at).toLocaleDateString()}</div>
            </div>
            <div class="user-actions">
                <span class="user-role ${user.role}">${user.role}</span>
                ${user.id !== currentUser.id ? `
                    <button class="btn btn-sm btn-warning" onclick="toggleUserRole('${user.id}', '${user.role}')">
                        ${user.role === 'admin' ? 'Demote' : 'Promote'}
                    </button>
                ` : '<span style="color:#8892b0;font-size:0.8rem;">You</span>'}
            </div>
        </div>
    `).join('');
}

async function toggleUserRole(userId, currentRole) {
    const newRole = currentRole === 'admin' ? 'renter' : 'admin';
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}/role`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ role: newRole })
        });
        
        if (response.ok) {
            showStatus(`User role updated to ${newRole}`, 'success');
            loadUsers();
        } else {
            const data = await response.json();
            showStatus(data.msg || 'Failed to update role', 'error');
        }
    } catch (error) {
        showStatus('Error updating user role', 'error');
    }
}

async function loadFleet() {
    const listDiv = document.getElementById('fleetList');
    listDiv.innerHTML = '<div class="loading-text">Loading fleet...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/view_all_available`);
        const scooters = await response.json();
        displayFleet(scooters);
    } catch (error) {
        listDiv.innerHTML = '<div class="empty-state">Error loading fleet</div>';
    }
}

function displayFleet(scooters) {
    const listDiv = document.getElementById('fleetList');
    
    if (!scooters || scooters.length === 0) {
        listDiv.innerHTML = '<div class="empty-state">No scooters in fleet</div>';
        return;
    }
    
    listDiv.innerHTML = scooters.map(scooter => `
        <div class="fleet-item">
            <div class="fleet-details">
                <div class="fleet-id">🛴 Scooter ${scooter.id}</div>
                <div class="fleet-location">📍 ${scooter.lat.toFixed(4)}, ${scooter.lng.toFixed(4)}</div>
            </div>
            <div class="fleet-actions">
                <span class="scooter-status ${scooter.is_reserved ? 'status-reserved' : 'status-available'}">
                    ${scooter.is_reserved ? 'Reserved' : 'Available'}
                </span>
                ${!scooter.is_reserved ? `
                    <button class="btn btn-sm btn-danger" onclick="deleteScooter('${scooter.id}')">Delete</button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

async function addScooter(id, lat, lng) {
    try {
        const response = await fetch(`${API_BASE}/admin/scooters`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ id, lat, lng })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('Scooter added successfully!', 'success');
            document.getElementById('addScooterForm').classList.add('hidden');
            document.getElementById('newScooterForm').reset();
            loadFleet();
            viewAllScooters();
        } else {
            showStatus(data.msg || 'Failed to add scooter', 'error');
        }
    } catch (error) {
        showStatus('Error adding scooter', 'error');
    }
}

async function deleteScooter(scooterId) {
    if (!confirm(`Are you sure you want to delete scooter ${scooterId}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/scooters/${scooterId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            showStatus(`Scooter ${scooterId} deleted`, 'success');
            loadFleet();
            viewAllScooters();
        } else {
            const data = await response.json();
            showStatus(data.msg || 'Failed to delete scooter', 'error');
        }
    } catch (error) {
        showStatus('Error deleting scooter', 'error');
    }
}

// ==================
// MAP FUNCTIONS
// ==================

function initMap() {
    map = L.map('map').setView([0, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
}

function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

function addScooterMarkers(scooters) {
    clearMarkers();
    
    if (scooters.length === 0) return;
    
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
                ${!isReserved && currentUser ? `<button class="popup-btn" onclick="reserveFromMap('${scooter.id}')">Reserve This Scooter</button>` : ''}
                ${!isReserved && !currentUser ? `<button class="popup-btn" onclick="showAuthModal()">Login to Reserve</button>` : ''}
            `);
        
        markers.push(marker);
    });
    
    if (markers.length > 0) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// ==================
// SCOOTER FUNCTIONS
// ==================

function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type} show`;
    
    setTimeout(() => {
        statusDiv.classList.remove('show');
    }, 5000);
}

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
                ${scooter.distance ? `<div class="scooter-distance">📏 ${scooter.distance.toFixed(0)}m away</div>` : ''}
            </div>
            <span class="scooter-status ${scooter.is_reserved ? 'status-reserved' : 'status-available'}">
                ${scooter.is_reserved ? 'Reserved' : 'Available'}
            </span>
        </div>
    `).join('');
}

function focusScooter(lat, lng) {
    map.setView([lat, lng], 15);
}

async function searchScooters(lat, lng, radius) {
    try {
        showStatus('Searching for scooters...', 'info');
        
        const response = await fetch(`${API_BASE}/search?lat=${lat}&lng=${lng}&radius=${radius}`);
        const data = await response.json();
        
        if (response.ok) {
            addScooterMarkers(data);
            
            // Add search location marker
            const searchIcon = L.divIcon({
                html: '<div style="background-color: #00c851; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.4);"></div>',
                className: 'search-marker',
                iconSize: [20, 20]
            });
            const searchMarker = L.marker([lat, lng], { icon: searchIcon })
                .addTo(map)
                .bindPopup('📍 Your Search Location');
            markers.push(searchMarker);
            
            // Draw search radius circle
            const circle = L.circle([lat, lng], {
                radius: radius,
                color: '#00c851',
                fillColor: '#00c851',
                fillOpacity: 0.1,
                weight: 2
            }).addTo(map);
            markers.push(circle);
            
            map.setView([lat, lng], 13);
            
            showStatus(`Found ${data.length} scooters within ${radius}m`, 'success');
            displayScooterList(data);
        } else {
            showStatus(data.msg || 'Search failed', 'error');
        }
    } catch (error) {
        showStatus('Error searching: ' + error.message, 'error');
    }
}

async function reserveScooter(scooterId) {
    if (!currentUser) {
        showAuthModal();
        return;
    }
    
    try {
        showStatus(`Reserving scooter ${scooterId}...`, 'info');
        
        const response = await fetch(`${API_BASE}/reservation/start?id=${scooterId}`);
        const data = await response.json();
        
        if (response.ok) {
            showStatus(data.msg, 'success');
            viewAllScooters();
            if (currentUser.role === 'admin') loadFleet();
        } else {
            showStatus(data.msg || 'Reservation failed', 'error');
        }
    } catch (error) {
        showStatus('Error reserving: ' + error.message, 'error');
    }
}

function reserveFromMap(scooterId) {
    document.getElementById('reserveId').value = scooterId;
    reserveScooter(scooterId);
}

async function endReservation(scooterId, lat, lng) {
    if (!currentUser) {
        showAuthModal();
        return;
    }
    
    try {
        showStatus(`Ending reservation for scooter ${scooterId}...`, 'info');
        
        const response = await fetch(`${API_BASE}/reservation/end?id=${scooterId}&lat=${lat}&lng=${lng}`);
        const data = await response.json();
        
        if (response.ok) {
            showStatus(`${data.msg} (Transaction ID: ${data.txn_id})`, 'success');
            viewAllScooters();
            if (currentUser.role === 'admin') loadFleet();
        } else {
            showStatus(data.msg || 'Failed to end reservation', 'error');
        }
    } catch (error) {
        showStatus('Error ending reservation: ' + error.message, 'error');
    }
}

function getUserLocation(callback) {
    if (navigator.geolocation) {
        showStatus('Getting your location...', 'info');
        navigator.geolocation.getCurrentPosition(
            (position) => {
                callback(position.coords.latitude, position.coords.longitude);
                showStatus('Location acquired!', 'success');
            },
            (error) => {
                showStatus('Unable to get your location: ' + error.message, 'error');
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    } else {
        showStatus('Geolocation is not supported by your browser', 'error');
    }
}

// ==================
// ENHANCED SEARCH FEATURES
// ==================

// One-click Find Near Me
function findNearMe() {
    showStatus('🎯 Finding scooters near you...', 'info');
    
    if (!navigator.geolocation) {
        showStatus('Geolocation is not supported by your browser', 'error');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            showStatus(`📍 Location found! Searching within ${searchRadius}m...`, 'info');
            
            // Add user location marker
            addUserLocationMarker(lat, lng);
            
            // Search for scooters
            await searchScooters(lat, lng, searchRadius);
        },
        (error) => {
            let errorMsg = 'Unable to get your location';
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMsg = 'Location access denied. Please enable location permissions.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMsg = 'Location information unavailable.';
                    break;
                case error.TIMEOUT:
                    errorMsg = 'Location request timed out.';
                    break;
            }
            showStatus(errorMsg, 'error');
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

// Add user location marker
function addUserLocationMarker(lat, lng) {
    const userIcon = L.divIcon({
        html: `<div style="
            background: linear-gradient(135deg, #00c851, #007e33);
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 4px solid white;
            box-shadow: 0 0 20px rgba(0, 200, 81, 0.6), 0 3px 10px rgba(0,0,0,0.4);
            animation: pulse 2s infinite;
        "></div>
        <style>
            @keyframes pulse {
                0% { box-shadow: 0 0 20px rgba(0, 200, 81, 0.6), 0 3px 10px rgba(0,0,0,0.4); }
                50% { box-shadow: 0 0 30px rgba(0, 200, 81, 0.9), 0 3px 10px rgba(0,0,0,0.4); }
                100% { box-shadow: 0 0 20px rgba(0, 200, 81, 0.6), 0 3px 10px rgba(0,0,0,0.4); }
            }
        </style>`,
        className: 'user-location-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
    
    const userMarker = L.marker([lat, lng], { icon: userIcon })
        .addTo(map)
        .bindPopup('<div class="popup-title">📍 Your Location</div>');
    markers.push(userMarker);
}

// Address Search with Geocoding (Nominatim)
async function geocodeAddress(query) {
    if (!query || query.length < 3) return [];
    
    try {
        const response = await fetch(
            `${NOMINATIM_API}/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`,
            { headers: { 'Accept-Language': 'en' } }
        );
        
        if (!response.ok) throw new Error('Geocoding failed');
        
        return await response.json();
    } catch (error) {
        console.error('Geocoding error:', error);
        return [];
    }
}

function showAddressSuggestions(suggestions) {
    const container = document.getElementById('addressSuggestions');
    
    if (!suggestions || suggestions.length === 0) {
        container.classList.add('hidden');
        return;
    }
    
    container.innerHTML = suggestions.map(place => `
        <div class="suggestion-item" data-lat="${place.lat}" data-lng="${place.lon}">
            <div class="suggestion-name">${place.display_name.split(',')[0]}</div>
            <div class="suggestion-detail">${place.display_name.split(',').slice(1, 3).join(',')}</div>
        </div>
    `).join('');
    
    container.classList.remove('hidden');
    
    // Add click handlers
    container.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            const lat = parseFloat(item.dataset.lat);
            const lng = parseFloat(item.dataset.lng);
            const name = item.querySelector('.suggestion-name').textContent;
            
            document.getElementById('addressInput').value = name;
            container.classList.add('hidden');
            
            searchAtLocation(lat, lng, name);
        });
    });
}

async function searchAtLocation(lat, lng, locationName) {
    const radius = parseInt(document.getElementById('addressRadius').value) || 2000;
    
    showStatus(`🔍 Searching near ${locationName}...`, 'info');
    
    // Clear and add location marker
    clearMarkers();
    
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
        .bindPopup(`<div class="popup-title">📍 ${locationName}</div>`);
    markers.push(locationMarker);
    
    await searchScooters(lat, lng, radius);
}

// Region Quick Select
function goToRegion() {
    const select = document.getElementById('regionSelect');
    const value = select.value;
    
    if (!value) {
        showStatus('Please select a region', 'info');
        return;
    }
    
    const [lat, lng] = value.split(',').map(Number);
    const regionName = select.options[select.selectedIndex].text;
    
    showStatus(`🗺️ Going to ${regionName}...`, 'info');
    
    map.setView([lat, lng], 12);
    searchScooters(lat, lng, 5000); // 5km radius for regions
}

// Click on Map Search
function enableMapClickSearch() {
    map.on('click', onMapClick);
}

function onMapClick(e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    
    // Remove previous click marker if exists
    if (clickSearchMarker) {
        map.removeLayer(clickSearchMarker);
    }
    
    // Create click marker with search popup
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
    
    clickSearchMarker = L.marker([lat, lng], { icon: clickIcon })
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
}

async function searchFromMapClick(lat, lng) {
    const radiusSelect = document.getElementById('clickRadius');
    const radius = radiusSelect ? parseInt(radiusSelect.value) : 1000;
    
    // Close popup
    if (clickSearchMarker) {
        clickSearchMarker.closePopup();
    }
    
    showStatus(`🔍 Searching at clicked location...`, 'info');
    await searchScooters(lat, lng, radius);
}


// ==================
// EVENT LISTENERS
// ==================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize map
    initMap();
    
    // Enable click-on-map search
    enableMapClickSearch();
    
    // Check auth status
    checkAuthStatus();
    
    // Load all scooters
    viewAllScooters();
    
    // ==================
    // SEARCH TABS
    // ==================
    
    document.querySelectorAll('.search-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active tab
            document.querySelectorAll('.search-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.search-tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab + 'Tab').classList.add('active');
        });
    });
    
    // ==================
    // ENHANCED SEARCH EVENT LISTENERS
    // ==================
    
    // Find Near Me button
    document.getElementById('findNearMeBtn').addEventListener('click', findNearMe);
    
    // Radius selector buttons
    document.querySelectorAll('.radius-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.radius-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            searchRadius = parseInt(btn.dataset.radius);
        });
    });
    
    // Address search with debounce
    const addressInput = document.getElementById('addressInput');
    addressInput.addEventListener('input', (e) => {
        clearTimeout(addressSearchTimeout);
        const query = e.target.value.trim();
        
        if (query.length < 3) {
            document.getElementById('addressSuggestions').classList.add('hidden');
            return;
        }
        
        document.getElementById('addressSuggestions').innerHTML = 
            '<div class="suggestions-loading">Searching...</div>';
        document.getElementById('addressSuggestions').classList.remove('hidden');
        
        addressSearchTimeout = setTimeout(async () => {
            const suggestions = await geocodeAddress(query);
            showAddressSuggestions(suggestions);
        }, 300);
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-input-wrapper') && !e.target.closest('.suggestions-list')) {
            document.getElementById('addressSuggestions').classList.add('hidden');
        }
    });
    
    // Address search form submit
    document.getElementById('addressSearchForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = addressInput.value.trim();
        if (!query) return;
        
        showStatus('🔍 Searching for location...', 'info');
        const results = await geocodeAddress(query);
        
        if (results.length > 0) {
            const place = results[0];
            searchAtLocation(parseFloat(place.lat), parseFloat(place.lon), place.display_name.split(',')[0]);
        } else {
            showStatus('Location not found. Try a different search.', 'error');
        }
    });
    
    // Region select
    document.getElementById('goToRegionBtn').addEventListener('click', goToRegion);
    document.getElementById('regionSelect').addEventListener('change', (e) => {
        if (e.target.value) goToRegion();
    });
    
    // Auth modal tabs
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab + 'Form').classList.add('active');
        });
    });
    
    // Login form
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        const errorDiv = document.getElementById('loginError');
        
        const result = await login(email, password);
        if (!result.success) {
            errorDiv.textContent = result.error;
            errorDiv.classList.add('show');
        }
    });
    
    // Register form
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('registerName').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const errorDiv = document.getElementById('registerError');
        
        const result = await register(name, email, password);
        if (!result.success) {
            errorDiv.textContent = result.error;
            errorDiv.classList.add('show');
        }
    });
    
    // Show login modal
    document.getElementById('showLoginBtn').addEventListener('click', showAuthModal);
    
    // Login links in login prompts
    document.querySelectorAll('.login-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            showAuthModal();
        });
    });
    
    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', logout);
    
    // Close modal on outside click
    document.getElementById('authModal').addEventListener('click', (e) => {
        if (e.target.id === 'authModal') {
            hideAuthModal();
        }
    });
    
    // Admin tabs
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.admin-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.panel + 'Panel').classList.add('active');
        });
    });
    
    // Admin refresh buttons
    document.getElementById('refreshUsersBtn').addEventListener('click', loadUsers);
    document.getElementById('refreshFleetBtn').addEventListener('click', loadFleet);
    
    // Add scooter form toggle
    document.getElementById('showAddScooterBtn').addEventListener('click', () => {
        document.getElementById('addScooterForm').classList.toggle('hidden');
    });
    
    document.getElementById('cancelAddScooter').addEventListener('click', () => {
        document.getElementById('addScooterForm').classList.add('hidden');
    });
    
    // Add scooter form submit
    document.getElementById('newScooterForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const id = document.getElementById('newScooterId').value;
        const lat = parseFloat(document.getElementById('newScooterLat').value);
        const lng = parseFloat(document.getElementById('newScooterLng').value);
        addScooter(id, lat, lng);
    });
    
    // View All button
    document.getElementById('viewAllBtn').addEventListener('click', viewAllScooters);
    
    // Advanced search form
    document.getElementById('searchForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const latVal = document.getElementById('searchLat').value;
        const lngVal = document.getElementById('searchLng').value;
        
        if (!latVal || !lngVal) {
            showStatus('Please enter both latitude and longitude', 'error');
            return;
        }
        
        const lat = parseFloat(latVal);
        const lng = parseFloat(lngVal);
        const radius = parseInt(document.getElementById('searchRadius').value) || 5000;
        
        if (isNaN(lat) || isNaN(lng)) {
            showStatus('Invalid coordinates', 'error');
            return;
        }
        
        searchScooters(lat, lng, radius);
    });
    
    // Use location button for advanced search
    document.getElementById('useLocationBtn').addEventListener('click', () => {
        getUserLocation((lat, lng) => {
            document.getElementById('searchLat').value = lat.toFixed(6);
            document.getElementById('searchLng').value = lng.toFixed(6);
            showStatus('Coordinates filled! Click "Search Coordinates" to search.', 'success');
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
