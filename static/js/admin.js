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
 * Load fleet (all scooters)
 */
async function loadFleet() {
    const listDiv = document.getElementById('fleetList');
    listDiv.innerHTML = '<div class="loading-text">Loading fleet...</div>';
    
    const result = await apiGet('/view_all_available');
    
    if (result.ok) {
        displayFleet(result.data);
    } else {
        listDiv.innerHTML = '<div class="empty-state">Error loading fleet</div>';
    }
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

