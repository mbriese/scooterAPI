/**
 * Admin Module - Admin dashboard functions
 */

/**
 * Load all admin data
 */
async function loadAdminData() {
    await loadUsers();
    await loadFleet();
}

/**
 * Load users list
 */
async function loadUsers() {
    const listDiv = document.getElementById('usersList');
    listDiv.innerHTML = '<div class="loading-text">Loading users...</div>';
    
    const result = await apiGet('/admin/users');
    
    if (result.ok) {
        displayUsers(result.data.users);
    } else {
        listDiv.innerHTML = '<div class="empty-state">Failed to load users</div>';
    }
}

/**
 * Display users in the admin panel
 */
function displayUsers(users) {
    const listDiv = document.getElementById('usersList');
    const currentUserId = getCurrentUser()?.id;
    
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
                ${user.id !== currentUserId ? `
                    <button class="btn btn-sm btn-warning" onclick="toggleUserRole('${user.id}', '${user.role}')">
                        ${user.role === 'admin' ? 'Demote' : 'Promote'}
                    </button>
                ` : '<span style="color:#8892b0;font-size:0.8rem;">You</span>'}
            </div>
        </div>
    `).join('');
}

/**
 * Toggle user role between admin and renter
 */
async function toggleUserRole(userId, currentRole) {
    const newRole = currentRole === 'admin' ? 'renter' : 'admin';
    
    const result = await apiPut(`/admin/users/${userId}/role`, { role: newRole });
    
    if (result.ok) {
        showStatus(`User role updated to ${newRole}`, 'success');
        loadUsers();
    } else {
        showStatus(result.error || 'Failed to update role', 'error');
    }
}

/**
 * Load fleet (all scooters - available AND reserved)
 */
async function loadFleet() {
    const listDiv = document.getElementById('fleetList');
    listDiv.innerHTML = '<div class="loading-text">Loading fleet...</div>';
    
    const result = await apiGet('/admin/scooters');
    
    if (result.ok) {
        displayFleetStats(result.data.stats);
        displayFleet(result.data.scooters);
    } else {
        listDiv.innerHTML = '<div class="empty-state">Error loading fleet</div>';
    }
}

/**
 * Display fleet statistics
 */
function displayFleetStats(stats) {
    let statsDiv = document.getElementById('fleetStats');
    
    // Create stats div if it doesn't exist
    if (!statsDiv) {
        statsDiv = document.createElement('div');
        statsDiv.id = 'fleetStats';
        statsDiv.className = 'fleet-stats';
        const fleetList = document.getElementById('fleetList');
        fleetList.parentNode.insertBefore(statsDiv, fleetList);
    }
    
    statsDiv.innerHTML = `
        <div class="stat-item">
            <span class="stat-value">${stats.total}</span>
            <span class="stat-label">Total</span>
        </div>
        <div class="stat-item available">
            <span class="stat-value">${stats.available}</span>
            <span class="stat-label">Available</span>
        </div>
        <div class="stat-item reserved">
            <span class="stat-value">${stats.reserved}</span>
            <span class="stat-label">Reserved</span>
        </div>
    `;
}

/**
 * Display fleet in the admin panel
 */
function displayFleet(scooters) {
    const listDiv = document.getElementById('fleetList');
    
    if (!scooters || scooters.length === 0) {
        listDiv.innerHTML = '<div class="empty-state">No scooters in fleet</div>';
        return;
    }
    
    // Sort: available first, then reserved
    const sorted = [...scooters].sort((a, b) => {
        if (a.is_reserved === b.is_reserved) return 0;
        return a.is_reserved ? 1 : -1;
    });
    
    listDiv.innerHTML = sorted.map(scooter => `
        <div class="fleet-item ${scooter.is_reserved ? 'fleet-reserved' : ''}">
            <div class="fleet-details">
                <div class="fleet-id">🛴 Scooter ${scooter.id}</div>
                <div class="fleet-location">📍 ${scooter.lat.toFixed(4)}, ${scooter.lng.toFixed(4)}</div>
            </div>
            <div class="fleet-actions">
                <span class="scooter-status ${scooter.is_reserved ? 'status-reserved' : 'status-available'}">
                    ${scooter.is_reserved ? '🔒 Reserved' : '✅ Available'}
                </span>
                ${!scooter.is_reserved ? `
                    <button class="btn btn-sm btn-secondary" onclick="showMoveScooterModal('${scooter.id}')" title="Move to new location">
                        📍 Move
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteScooter('${scooter.id}')">Delete</button>
                ` : `
                    <button class="btn btn-sm btn-warning" onclick="forceEndReservation('${scooter.id}')" title="Force end reservation">
                        Release
                    </button>
                `}
            </div>
        </div>
    `).join('');
}

// City/Region data for moving scooters
const CITY_LOCATIONS = {
    // US Cities
    'New York City, NY': { lat: 40.7128, lng: -74.0060 },
    'Los Angeles, CA': { lat: 34.0522, lng: -118.2437 },
    'Chicago, IL': { lat: 41.8781, lng: -87.6298 },
    'Houston, TX': { lat: 29.7604, lng: -95.3698 },
    'Phoenix, AZ': { lat: 33.4484, lng: -112.0740 },
    'San Francisco, CA': { lat: 37.7749, lng: -122.4194 },
    'Seattle, WA': { lat: 47.6062, lng: -122.3321 },
    'Miami, FL': { lat: 25.7617, lng: -80.1918 },
    'Denver, CO': { lat: 39.7392, lng: -104.9903 },
    'Austin, TX': { lat: 30.2672, lng: -97.7431 },
    // Europe
    'London, UK': { lat: 51.5074, lng: -0.1278 },
    'Paris, France': { lat: 48.8566, lng: 2.3522 },
    'Berlin, Germany': { lat: 52.5200, lng: 13.4050 },
    'Rome, Italy': { lat: 41.9028, lng: 12.4964 },
    'Amsterdam, Netherlands': { lat: 52.3676, lng: 4.9041 },
    'Madrid, Spain': { lat: 40.4168, lng: -3.7038 },
    // Asia Pacific
    'Tokyo, Japan': { lat: 35.6762, lng: 139.6503 },
    'Hong Kong': { lat: 22.3193, lng: 114.1694 },
    'Singapore': { lat: 1.3521, lng: 103.8198 },
    'Sydney, Australia': { lat: -33.8688, lng: 151.2093 }
};

let moveScooterId = null;

/**
 * Show the move scooter modal
 */
function showMoveScooterModal(scooterId) {
    moveScooterId = scooterId;
    
    // Create modal if it doesn't exist
    let modal = document.getElementById('moveScooterModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'moveScooterModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content move-scooter-modal">
                <h2>📍 Move Scooter</h2>
                <p class="modal-subtitle">Select a city or enter custom coordinates</p>
                
                <div class="move-tabs">
                    <button class="move-tab active" data-tab="city">By City</button>
                    <button class="move-tab" data-tab="coords">By Coordinates</button>
                </div>
                
                <div id="moveCityTab" class="move-tab-content active">
                    <div class="form-group">
                        <label>Select City:</label>
                        <select id="moveCitySelect" class="region-dropdown">
                            <option value="">-- Choose a City --</option>
                            <optgroup label="🇺🇸 United States">
                                <option value="New York City, NY">New York City, NY</option>
                                <option value="Los Angeles, CA">Los Angeles, CA</option>
                                <option value="Chicago, IL">Chicago, IL</option>
                                <option value="Houston, TX">Houston, TX</option>
                                <option value="Phoenix, AZ">Phoenix, AZ</option>
                                <option value="San Francisco, CA">San Francisco, CA</option>
                                <option value="Seattle, WA">Seattle, WA</option>
                                <option value="Miami, FL">Miami, FL</option>
                                <option value="Denver, CO">Denver, CO</option>
                                <option value="Austin, TX">Austin, TX</option>
                            </optgroup>
                            <optgroup label="🇪🇺 Europe">
                                <option value="London, UK">London, UK</option>
                                <option value="Paris, France">Paris, France</option>
                                <option value="Berlin, Germany">Berlin, Germany</option>
                                <option value="Rome, Italy">Rome, Italy</option>
                                <option value="Amsterdam, Netherlands">Amsterdam, Netherlands</option>
                                <option value="Madrid, Spain">Madrid, Spain</option>
                            </optgroup>
                            <optgroup label="🌏 Asia Pacific">
                                <option value="Tokyo, Japan">Tokyo, Japan</option>
                                <option value="Hong Kong">Hong Kong</option>
                                <option value="Singapore">Singapore</option>
                                <option value="Sydney, Australia">Sydney, Australia</option>
                            </optgroup>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="moveRandomOffset" checked>
                            Add small random offset (so scooters don't stack)
                        </label>
                    </div>
                </div>
                
                <div id="moveCoordsTab" class="move-tab-content">
                    <div class="form-row-compact">
                        <div class="form-group compact">
                            <label>Latitude:</label>
                            <input type="number" id="moveLatInput" step="any" placeholder="40.7128">
                        </div>
                        <div class="form-group compact">
                            <label>Longitude:</label>
                            <input type="number" id="moveLngInput" step="any" placeholder="-74.0060">
                        </div>
                    </div>
                </div>
                
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="confirmMoveScooter()">Move Scooter</button>
                    <button class="btn btn-secondary" onclick="hideMoveScooterModal()">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Add tab switching
        modal.querySelectorAll('.move-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                modal.querySelectorAll('.move-tab').forEach(t => t.classList.remove('active'));
                modal.querySelectorAll('.move-tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById('move' + tab.dataset.tab.charAt(0).toUpperCase() + tab.dataset.tab.slice(1) + 'Tab').classList.add('active');
            });
        });
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) hideMoveScooterModal();
        });
    }
    
    // Reset form
    document.getElementById('moveCitySelect').value = '';
    document.getElementById('moveLatInput').value = '';
    document.getElementById('moveLngInput').value = '';
    document.getElementById('moveRandomOffset').checked = true;
    
    // Show modal
    modal.classList.add('show');
}

/**
 * Hide the move scooter modal
 */
function hideMoveScooterModal() {
    const modal = document.getElementById('moveScooterModal');
    if (modal) modal.classList.remove('show');
    moveScooterId = null;
}

/**
 * Confirm and execute the scooter move
 */
async function confirmMoveScooter() {
    if (!moveScooterId) return;
    
    let lat, lng;
    const cityTab = document.getElementById('moveCityTab');
    
    if (cityTab.classList.contains('active')) {
        // Moving by city
        const citySelect = document.getElementById('moveCitySelect');
        const cityName = citySelect.value;
        
        if (!cityName || !CITY_LOCATIONS[cityName]) {
            showStatus('Please select a city', 'error');
            return;
        }
        
        lat = CITY_LOCATIONS[cityName].lat;
        lng = CITY_LOCATIONS[cityName].lng;
        
        // Add random offset if checked (within ~500m)
        if (document.getElementById('moveRandomOffset').checked) {
            lat += (Math.random() - 0.5) * 0.01;  // ~500m variation
            lng += (Math.random() - 0.5) * 0.01;
        }
    } else {
        // Moving by coordinates
        lat = parseFloat(document.getElementById('moveLatInput').value);
        lng = parseFloat(document.getElementById('moveLngInput').value);
        
        if (isNaN(lat) || isNaN(lng)) {
            showStatus('Please enter valid coordinates', 'error');
            return;
        }
    }
    
    // Call API to update scooter location
    const result = await apiPut(`/admin/scooters/${moveScooterId}`, { lat, lng });
    
    if (result.ok) {
        showStatus(`Scooter ${moveScooterId} moved successfully!`, 'success');
        hideMoveScooterModal();
        loadFleet();
        viewAllScooters();
    } else {
        showStatus(result.error || 'Failed to move scooter', 'error');
    }
}

/**
 * Add a new scooter
 */
async function addScooter(id, lat, lng) {
    const result = await apiPost('/admin/scooters', { id, lat, lng });
    
    if (result.ok) {
        showStatus('Scooter added successfully!', 'success');
        document.getElementById('addScooterForm').classList.add('hidden');
        document.getElementById('newScooterForm').reset();
        loadFleet();
        viewAllScooters();
    } else {
        showStatus(result.error || 'Failed to add scooter', 'error');
    }
}

/**
 * Force end a reservation (admin only)
 */
async function forceEndReservation(scooterId) {
    if (!confirm(`Force release scooter ${scooterId}? This will end the reservation without payment.`)) {
        return;
    }
    
    const result = await apiPut(`/admin/scooters/${scooterId}/release`, {});
    
    if (result.ok) {
        showStatus(`Scooter ${scooterId} released`, 'success');
        loadFleet();
        viewAllScooters();
    } else {
        showStatus(result.error || 'Failed to release scooter', 'error');
    }
}

/**
 * Delete a scooter
 */
async function deleteScooter(scooterId) {
    if (!confirm(`Are you sure you want to delete scooter ${scooterId}?`)) {
        return;
    }
    
    const result = await apiDelete(`/admin/scooters/${scooterId}`);
    
    if (result.ok) {
        showStatus(`Scooter ${scooterId} deleted`, 'success');
        loadFleet();
        viewAllScooters();
    } else {
        showStatus(result.error || 'Failed to delete scooter', 'error');
    }
}

