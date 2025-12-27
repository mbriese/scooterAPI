// API Base URL
const API_BASE = window.location.origin;

// App State
let currentUser = null;
let map;
let markers = [];

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
            }
        );
    } else {
        showStatus('Geolocation is not supported by your browser', 'error');
    }
}

// ==================
// EVENT LISTENERS
// ==================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize map
    initMap();
    
    // Check auth status
    checkAuthStatus();
    
    // Load all scooters
    viewAllScooters();
    
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
