/**
 * Main Module - Application initialization and event listeners
 * 
 * This file ties together all the modules and sets up event listeners.
 * Load order matters! This file should be loaded last.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ==================
    // INITIALIZATION
    // ==================
    
    initMap();
    enableMapClickSearch();
    checkAuthStatus();
    viewAllScooters();
    loadPricingInfo();
    
    // Check for active rental after auth check completes
    setTimeout(() => {
        if (isLoggedIn()) {
            checkActiveRental();
        }
    }, 500);
    
    // ==================
    // SEARCH TABS
    // ==================
    
    document.querySelectorAll('.search-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.search-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.search-tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab + 'Tab').classList.add('active');
        });
    });
    
    // ==================
    // FIND NEAR ME
    // ==================
    
    document.getElementById('findNearMeBtn').addEventListener('click', findNearMe);
    
    // Radius selector buttons
    document.querySelectorAll('.radius-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.radius-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setSearchRadius(parseInt(btn.dataset.radius));
        });
    });
    
    // ==================
    // ADDRESS SEARCH
    // ==================
    
    const addressInput = document.getElementById('addressInput');
    
    addressInput.addEventListener('input', (e) => {
        clearTimeout(getAddressSearchTimeout());
        const query = e.target.value.trim();
        
        if (query.length < 3) {
            document.getElementById('addressSuggestions').classList.add('hidden');
            return;
        }
        
        document.getElementById('addressSuggestions').innerHTML = 
            '<div class="suggestions-loading">Searching...</div>';
        document.getElementById('addressSuggestions').classList.remove('hidden');
        
        setAddressSearchTimeout(setTimeout(async () => {
            const suggestions = await geocodeAddress(query);
            showAddressSuggestions(suggestions);
        }, 300));
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
    
    // ==================
    // REGION SELECT
    // ==================
    
    document.getElementById('goToRegionBtn').addEventListener('click', goToRegion);
    document.getElementById('regionSelect').addEventListener('change', (e) => {
        if (e.target.value) goToRegion();
    });
    
    // ==================
    // COORDINATE SEARCH
    // ==================
    
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
    
    document.getElementById('useLocationBtn').addEventListener('click', () => {
        getUserLocation((lat, lng) => {
            document.getElementById('searchLat').value = lat.toFixed(6);
            document.getElementById('searchLng').value = lng.toFixed(6);
            showStatus('Coordinates filled!', 'success');
        });
    });
    
    // ==================
    // AUTH MODAL
    // ==================
    
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab + 'Form').classList.add('active');
        });
    });
    
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
    
    document.getElementById('showLoginBtn').addEventListener('click', showAuthModal);
    
    document.querySelectorAll('.login-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            showAuthModal();
        });
    });
    
    document.getElementById('logoutBtn').addEventListener('click', logout);
    
    document.getElementById('authModal').addEventListener('click', (e) => {
        if (e.target.id === 'authModal') {
            hideAuthModal();
        }
    });
    
    // ==================
    // ADMIN PANEL
    // ==================
    
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.admin-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.panel + 'Panel').classList.add('active');
        });
    });
    
    document.getElementById('refreshUsersBtn').addEventListener('click', loadUsers);
    document.getElementById('refreshFleetBtn').addEventListener('click', loadFleet);
    
    document.getElementById('showAddScooterBtn').addEventListener('click', () => {
        document.getElementById('addScooterForm').classList.toggle('hidden');
    });
    
    document.getElementById('cancelAddScooter').addEventListener('click', () => {
        document.getElementById('addScooterForm').classList.add('hidden');
    });
    
    // Add Scooter location tabs
    document.querySelectorAll('.add-loc-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.add-loc-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.add-loc-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('add' + tab.dataset.tab.charAt(0).toUpperCase() + tab.dataset.tab.slice(1) + 'Tab').classList.add('active');
        });
    });
    
    document.getElementById('newScooterForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const id = document.getElementById('newScooterId').value;
        
        // Check which tab is active
        const cityTabActive = document.getElementById('addCityTab').classList.contains('active');
        
        if (cityTabActive) {
            // Add by city
            const citySelect = document.getElementById('addScooterCity');
            const cityName = citySelect.value;
            
            const cityData = getCityCoords(cityName);
            if (!cityName || !cityData) {
                showStatus('Please select a city', 'error');
                return;
            }
            
            let lat = cityData.lat;
            let lng = cityData.lng;
            
            // Add random offset if checked
            if (document.getElementById('addRandomOffset').checked) {
                lat += (Math.random() - 0.5) * 0.01;
                lng += (Math.random() - 0.5) * 0.01;
            }
            
            addScooter(id, lat, lng);
        } else {
            // Add by coordinates
            const lat = parseFloat(document.getElementById('newScooterLat').value);
            const lng = parseFloat(document.getElementById('newScooterLng').value);
            
            if (isNaN(lat) || isNaN(lng)) {
                showStatus('Please enter valid coordinates', 'error');
                return;
            }
            
            addScooter(id, lat, lng);
        }
    });
    
    // ==================
    // SCOOTER ACTIONS
    // ==================
    
    document.getElementById('viewAllBtn').addEventListener('click', viewAllScooters);
    
    document.getElementById('reserveForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const scooterId = document.getElementById('reserveId').value;
        reserveScooter(scooterId);
    });
    
    document.getElementById('endForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const scooterId = document.getElementById('endId').value;
        const lat = parseFloat(document.getElementById('endLat').value);
        const lng = parseFloat(document.getElementById('endLng').value);
        endReservation(scooterId, lat, lng);
    });
    
    // End active rental button
    document.getElementById('endActiveRentalBtn')?.addEventListener('click', () => {
        endActiveRental();
    });
    
    document.getElementById('useEndLocationBtn').addEventListener('click', () => {
        getUserLocation((lat, lng) => {
            document.getElementById('endLat').value = lat.toFixed(6);
            document.getElementById('endLng').value = lng.toFixed(6);
        });
    });
});

