/**
 * Scooters Module - Scooter viewing and reservation
 */

/**
 * View all available scooters
 */
async function viewAllScooters() {
    showStatus('Loading available scooters...', 'info');
    
    const result = await apiGet('/view_all_available');
    
    if (result.ok) {
        const scooters = result.data;
        displayScooterList(scooters);
        addScooterMarkers(scooters);
        showStatus(`Found ${scooters.length} available scooters`, 'success');
    } else {
        showStatus(result.error || 'Failed to load scooters', 'error');
    }
}

/**
 * Reserve a scooter
 */
async function reserveScooter(scooterId) {
    if (!isLoggedIn()) {
        showAuthModal();
        return;
    }
    
    showStatus(`Reserving scooter ${scooterId}...`, 'info');
    
    const result = await apiGet(`/reservation/start?id=${scooterId}`);
    
    if (result.ok) {
        showStatus(result.data.msg, 'success');
        viewAllScooters();
        if (isAdmin()) loadFleet();
    } else {
        showStatus(result.error || 'Reservation failed', 'error');
    }
}

/**
 * Reserve from map popup
 */
function reserveFromMap(scooterId) {
    document.getElementById('reserveId').value = scooterId;
    reserveScooter(scooterId);
}

/**
 * End a reservation
 */
async function endReservation(scooterId, lat, lng) {
    if (!isLoggedIn()) {
        showAuthModal();
        return;
    }
    
    showStatus(`Ending reservation for scooter ${scooterId}...`, 'info');
    
    const result = await apiGet(`/reservation/end?id=${scooterId}&lat=${lat}&lng=${lng}`);
    
    if (result.ok) {
        showStatus(`${result.data.msg} (Transaction ID: ${result.data.txn_id})`, 'success');
        viewAllScooters();
        if (isAdmin()) loadFleet();
    } else {
        showStatus(result.error || 'Failed to end reservation', 'error');
    }
}

