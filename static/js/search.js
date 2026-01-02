/**
 * Search Module - Search functionality
 */

/**
 * Search for scooters at a location
 */
async function searchScooters(lat, lng, radius) {
    // Validate coordinates before making API call
    const coordValidation = validateCoordinates(lat, lng);
    if (!coordValidation.valid) {
        showStatus(`Invalid coordinates: ${coordValidation.error}`, 'error');
        return;
    }
    
    // Validate radius
    const radiusValidation = validateRadius(radius);
    if (!radiusValidation.valid) {
        showStatus(`Invalid radius: ${radiusValidation.error}`, 'error');
        return;
    }
    
    // Use validated values
    lat = coordValidation.lat;
    lng = coordValidation.lng;
    radius = radiusValidation.radius;
    
    showStatus('Searching for scooters...', 'info');
    
    const result = await apiGet(`/search?lat=${lat}&lng=${lng}&radius=${radius}`);
    
    if (result.ok) {
        const scooters = result.data;
        
        addScooterMarkers(scooters);
        
        // Add search location marker
        const searchIcon = L.divIcon({
            html: '<div style="background-color: #00c851; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.4);"></div>',
            className: 'search-marker',
            iconSize: [20, 20]
        });
        
        const map = getMap();
        const searchMarker = L.marker([lat, lng], { icon: searchIcon })
            .addTo(map)
            .bindPopup('📍 Search Location');
        addMarker(searchMarker);
        
        // Add search radius circle
        addSearchRadiusCircle(lat, lng, radius);
        
        map.setView([lat, lng], 13);
        
        showStatus(`Found ${scooters.length} scooters within ${radius}m`, 'success');
        displayScooterList(scooters);
    } else {
        showStatus(result.error || 'Search failed', 'error');
    }
}

/**
 * One-click Find Near Me
 */
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
            
            showStatus(`📍 Location found! Searching within ${getSearchRadius()}m...`, 'info');
            
            addUserLocationMarker(lat, lng);
            await searchScooters(lat, lng, getSearchRadius());
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

/**
 * Search at a geocoded location
 */
async function searchAtLocation(lat, lng, locationName) {
    const radius = parseInt(document.getElementById('addressRadius').value) || 2000;
    
    showStatus(`🔍 Searching near ${locationName}...`, 'info');
    
    clearMarkers();
    addSearchLocationMarker(lat, lng, locationName);
    await searchScooters(lat, lng, radius);
}

/**
 * Go to a predefined region
 */
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
    
    getMap().setView([lat, lng], 12);
    searchScooters(lat, lng, 5000);
}

/**
 * Search from map click
 */
async function searchFromMapClick(lat, lng) {
    const radiusSelect = document.getElementById('clickRadius');
    const radius = radiusSelect ? parseInt(radiusSelect.value) : 1000;
    
    const clickMarker = getClickSearchMarker();
    if (clickMarker) {
        clickMarker.closePopup();
    }
    
    showStatus(`🔍 Searching at clicked location...`, 'info');
    await searchScooters(lat, lng, radius);
}

/**
 * Get user's current location
 */
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


