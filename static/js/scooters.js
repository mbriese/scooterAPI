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

// Store current rental data
let currentRentalData = null;

/**
 * Check for active rental and update UI
 */
async function checkActiveRental() {
    if (!isLoggedIn()) {
        hideActiveRentalUI();
        return;
    }
    
    const result = await apiGet('/rentals/active');
    
    if (result.ok && result.data.has_active_rental) {
        currentRentalData = result.data.rental;
        showActiveRentalUI(result.data.rental, result.data.current_cost_estimate);
    } else {
        currentRentalData = null;
        hideActiveRentalUI();
    }
}

/**
 * Show active rental UI in the My Rental panel
 */
function showActiveRentalUI(rental, costEstimate) {
    // Update the My Rental tab badge
    const badge = document.getElementById('rentalBadge');
    if (badge) badge.classList.remove('hidden');
    
    // Hide "no rental" message, show active rental card
    const noRentalMsg = document.getElementById('noRentalMessage');
    const activeCard = document.getElementById('activeRentalCard');
    if (noRentalMsg) noRentalMsg.classList.add('hidden');
    if (activeCard) activeCard.classList.remove('hidden');
    
    // Update rental details
    const scooterIdEl = document.getElementById('activeScooterId2');
    if (scooterIdEl) scooterIdEl.textContent = `Scooter #${rental.scooter_id}`;
    
    const startTime = new Date(rental.start_time);
    
    // Update duration and cost
    updateActiveDurationDisplay(startTime);
    const costEl = document.getElementById('activeEstCost2');
    if (costEl) costEl.textContent = `$${costEstimate.total_cost.toFixed(2)}`;
    
    // Show pickup location
    const pickupEl = document.getElementById('pickupLocation');
    if (pickupEl && rental.start_location) {
        pickupEl.textContent = `${rental.start_location.lat.toFixed(4)}, ${rental.start_location.lng.toFixed(4)}`;
    }
    
    // Start updating duration every second
    if (activeRentalInterval) clearInterval(activeRentalInterval);
    activeRentalInterval = setInterval(() => {
        updateActiveDurationDisplay(startTime);
    }, 1000);
    
    // Auto-switch to My Rental tab if user just started a rental
    // (only if they're on the reserve panel)
    const reservePanel = document.getElementById('reservePanel');
    if (reservePanel && reservePanel.classList.contains('active')) {
        switchToPanel('myrental');
    }
}

/**
 * Update the active duration display
 */
function updateActiveDurationDisplay(startTime) {
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
    
    const durationEl = document.getElementById('activeDuration2');
    if (durationEl) durationEl.textContent = durationText;
}

/**
 * Hide active rental UI
 */
function hideActiveRentalUI() {
    // Hide the tab badge
    const badge = document.getElementById('rentalBadge');
    if (badge) badge.classList.add('hidden');
    
    // Show "no rental" message, hide active rental card
    const noRentalMsg = document.getElementById('noRentalMessage');
    const activeCard = document.getElementById('activeRentalCard');
    if (noRentalMsg) noRentalMsg.classList.remove('hidden');
    if (activeCard) activeCard.classList.add('hidden');
    
    if (activeRentalInterval) {
        clearInterval(activeRentalInterval);
        activeRentalInterval = null;
    }
    
    currentRentalData = null;
}

/**
 * Legacy function for backwards compatibility
 */
function hideActiveRentalBanner() {
    hideActiveRentalUI();
}

/**
 * Switch to a panel
 */
function switchToPanel(panelName) {
    // Update tab buttons
    document.querySelectorAll('.panel-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.panel === panelName);
    });
    
    // Update panel content
    document.querySelectorAll('.panel-content').forEach(panel => {
        panel.classList.toggle('active', panel.id === panelName + 'Panel');
    });
}

/**
 * Return scooter to start location
 */
async function returnToStartLocation() {
    if (!currentRentalData || !currentRentalData.start_location) {
        showStatus('No active rental or pickup location found', 'error');
        return;
    }
    
    const rental = currentRentalData;
    const startLoc = rental.start_location;
    
    showStatus('Ending rental and returning to pickup location...', 'info');
    endReservation(rental.scooter_id, startLoc.lat, startLoc.lng);
}

/**
 * End rental at user's current location
 */
function endAtMyLocation() {
    if (!currentRentalData) {
        showStatus('No active rental found', 'error');
        return;
    }
    
    getUserLocation(
        (lat, lng) => {
            endReservation(currentRentalData.scooter_id, lat, lng);
        },
        () => {
            showStatus('Could not get your location. Please enter coordinates manually.', 'error');
        }
    );
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
        showStatus(`${result.data.msg}`, 'success');
        
        // Refresh scooter list and check for active rental
        viewAllScooters();
        await checkActiveRental();
        
        // Switch to My Rental tab to show the new rental
        switchToPanel('myrental');
        
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

