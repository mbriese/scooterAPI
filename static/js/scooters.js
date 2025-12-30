/**
 * Scooters Module - Scooter viewing and reservation
 */

// Active rental update interval
let activeRentalInterval = null;

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
 * Load and display pricing info
 */
async function loadPricingInfo() {
    const result = await apiGet('/pricing');
    
    if (result.ok) {
        const summary = result.data.summary;
        document.getElementById('priceUnlock').textContent = summary.unlock_fee;
        document.getElementById('priceHourly').textContent = summary.hourly;
        document.getElementById('priceDaily').textContent = summary.daily;
        document.getElementById('priceWeekly').textContent = summary.weekly;
        document.getElementById('priceMonthly').textContent = summary.monthly;
    }
}

/**
 * Check for active rental and update UI
 */
async function checkActiveRental() {
    if (!isLoggedIn()) {
        hideActiveRentalBanner();
        return;
    }
    
    const result = await apiGet('/rentals/active');
    
    if (result.ok && result.data.has_active_rental) {
        showActiveRentalBanner(result.data.rental, result.data.current_cost_estimate);
    } else {
        hideActiveRentalBanner();
    }
}

/**
 * Show the active rental banner
 */
function showActiveRentalBanner(rental, costEstimate) {
    const banner = document.getElementById('activeRentalBanner');
    if (!banner) return;
    
    document.getElementById('activeScooterId').textContent = rental.scooter_id;
    
    const startTime = new Date(rental.start_time);
    document.getElementById('activeStartTime').textContent = startTime.toLocaleTimeString();
    
    updateActiveDuration(startTime);
    document.getElementById('activeEstCost').textContent = `$${costEstimate.total_cost.toFixed(2)}`;
    
    banner.classList.remove('hidden');
    
    // Start updating duration every second
    if (activeRentalInterval) clearInterval(activeRentalInterval);
    activeRentalInterval = setInterval(() => {
        updateActiveDuration(startTime);
        // Update cost estimate every 30 seconds
    }, 1000);
    
    // Hide the reserve section when there's an active rental
    document.getElementById('reserveSection').classList.add('hidden');
}

/**
 * Update the active duration display
 */
function updateActiveDuration(startTime) {
    const now = new Date();
    const diffMs = now - startTime;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    
    let durationText;
    if (diffHours > 0) {
        durationText = `${diffHours}h ${mins}m`;
    } else {
        durationText = `${mins} min`;
    }
    
    document.getElementById('activeDuration').textContent = durationText;
}

/**
 * Hide the active rental banner
 */
function hideActiveRentalBanner() {
    const banner = document.getElementById('activeRentalBanner');
    if (banner) banner.classList.add('hidden');
    
    if (activeRentalInterval) {
        clearInterval(activeRentalInterval);
        activeRentalInterval = null;
    }
    
    // Show reserve section when no active rental
    const reserveSection = document.getElementById('reserveSection');
    if (reserveSection) reserveSection.classList.remove('hidden');
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
        const pricing = result.data.pricing;
        showStatus(`${result.data.msg}`, 'success');
        
        // Refresh scooter list and check for active rental
        viewAllScooters();
        checkActiveRental();
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
        // Show rental receipt
        showRentalReceipt(result.data);
        
        // Refresh UI
        viewAllScooters();
        checkActiveRental();
        if (isAdmin()) loadFleet();
    } else {
        showStatus(result.error || 'Failed to end reservation', 'error');
    }
}

/**
 * End active rental with current location
 */
async function endActiveRental() {
    const result = await apiGet('/rentals/active');
    
    if (!result.ok || !result.data.has_active_rental) {
        showStatus('No active rental found', 'error');
        return;
    }
    
    const rental = result.data.rental;
    
    // Try to get user's location
    getUserLocation(
        (lat, lng) => {
            endReservation(rental.scooter_id, lat, lng);
        },
        () => {
            // On location error, prompt for manual entry
            document.getElementById('endId').value = rental.scooter_id;
            showStatus('Please enter the drop-off location manually', 'info');
            document.getElementById('endLat').focus();
        }
    );
}

/**
 * Show rental receipt modal
 */
function showRentalReceipt(data) {
    // Create or get receipt modal
    let modal = document.getElementById('receiptModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'receiptModal';
        modal.className = 'modal';
        document.body.appendChild(modal);
    }
    
    const cost = data.cost;
    const duration = data.duration;
    
    modal.innerHTML = `
        <div class="modal-content rental-receipt">
            <div class="receipt-header">
                <h3>✅ Rental Complete!</h3>
                <div class="receipt-txn">Transaction: ${data.transaction_id}</div>
            </div>
            <div class="receipt-body">
                <div class="receipt-row">
                    <span class="receipt-label">Scooter</span>
                    <span class="receipt-value">${data.scooter_id}</span>
                </div>
                <div class="receipt-row">
                    <span class="receipt-label">Duration</span>
                    <span class="receipt-value">${formatDuration(duration.minutes)}</span>
                </div>
                <div class="receipt-row">
                    <span class="receipt-label">Distance</span>
                    <span class="receipt-value">${(data.distance_traveled_m / 1000).toFixed(2)} km</span>
                </div>
                <div class="receipt-row">
                    <span class="receipt-label">Unlock Fee</span>
                    <span class="receipt-value">$${cost.unlock_fee.toFixed(2)}</span>
                </div>
                <div class="receipt-row">
                    <span class="receipt-label">Rental (${cost.pricing_tier})</span>
                    <span class="receipt-value">$${cost.rental_fee.toFixed(2)}</span>
                </div>
                <div class="receipt-row total">
                    <span class="receipt-label">Total Charged</span>
                    <span class="receipt-value">$${cost.total.toFixed(2)}</span>
                </div>
            </div>
            <button class="btn btn-primary" onclick="closeReceiptModal()">Done</button>
        </div>
    `;
    
    modal.classList.add('show');
    showStatus(`Rental complete! Total: $${cost.total.toFixed(2)}`, 'success');
}

/**
 * Close receipt modal
 */
function closeReceiptModal() {
    const modal = document.getElementById('receiptModal');
    if (modal) modal.classList.remove('show');
}

/**
 * Format duration in human-readable format
 */
function formatDuration(minutes) {
    if (minutes < 60) {
        return `${Math.round(minutes)} min`;
    } else if (minutes < 1440) {
        const hours = Math.floor(minutes / 60);
        const mins = Math.round(minutes % 60);
        return `${hours}h ${mins}m`;
    } else {
        const days = Math.floor(minutes / 1440);
        const hours = Math.floor((minutes % 1440) / 60);
        return `${days}d ${hours}h`;
    }
}

