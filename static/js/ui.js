/**
 * UI Module - User interface helpers
 */

/**
 * Show a status message
 */
function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type} show`;
    
    setTimeout(() => {
        statusDiv.classList.remove('show');
    }, 5000);
}

/**
 * Show the authentication modal
 */
function showAuthModal() {
    document.getElementById('authModal').classList.add('show');
}

/**
 * Hide the authentication modal
 */
function hideAuthModal() {
    document.getElementById('authModal').classList.remove('show');
    document.getElementById('loginForm').reset();
    document.getElementById('registerForm').reset();
    document.getElementById('loginError').classList.remove('show');
    document.getElementById('registerError').classList.remove('show');
}

/**
 * Update UI for logged in user
 */
function updateUIForLoggedInUser() {
    const user = getCurrentUser();
    
    // Hide login button, show user info
    document.getElementById('showLoginBtn').classList.add('hidden');
    document.getElementById('userInfo').classList.remove('hidden');
    
    // Update user info display
    document.getElementById('userName').textContent = user.name;
    const roleSpan = document.getElementById('userRole');
    roleSpan.textContent = user.role;
    roleSpan.className = `user-role ${user.role}`;
    
    // Show renter features
    document.querySelectorAll('.renter-feature').forEach(el => {
        el.querySelector('.login-prompt')?.classList.add('hidden');
        el.querySelector('form')?.classList.remove('hidden');
    });
    
    // Show/hide admin panel
    if (user.role === 'admin') {
        document.getElementById('adminPanel').classList.remove('hidden');
        loadAdminData();
    } else {
        document.getElementById('adminPanel').classList.add('hidden');
    }
}

/**
 * Update UI for logged out user
 */
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

/**
 * Display scooter list in the sidebar
 */
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

/**
 * Show address suggestions dropdown
 */
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

