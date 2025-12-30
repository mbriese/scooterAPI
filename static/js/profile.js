/**
 * Profile Module - User profile and payment management
 */

/**
 * Show the profile modal
 */
function showProfileModal() {
    const modal = document.getElementById('profileModal');
    if (modal) {
        modal.classList.add('show');
        loadProfile();
    }
}

/**
 * Hide the profile modal
 */
function hideProfileModal() {
    const modal = document.getElementById('profileModal');
    if (modal) modal.classList.remove('show');
}

/**
 * Load user profile data
 */
async function loadProfile() {
    const result = await apiGet('/profile');
    
    if (result.ok) {
        const profile = result.data.profile;
        
        // Update account tab
        document.getElementById('profileName').textContent = profile.name || '--';
        document.getElementById('profileEmail').textContent = profile.email || '--';
        document.getElementById('profileCreated').textContent = formatDate(profile.created_at);
        
        // Update payment tab
        updatePaymentDisplay(profile.payment_method);
        
        // Update address tab - ALWAYS set values (clear if no address)
        const address = profile.address || {};
        document.getElementById('addressStreet').value = address.street || '';
        document.getElementById('addressCity').value = address.city || '';
        document.getElementById('addressState').value = address.state || '';
        document.getElementById('addressZip').value = address.zip_code || '';
        document.getElementById('addressPhone').value = address.phone || '';
    } else {
        // Clear all fields if profile load fails
        clearProfileForm();
    }
}

/**
 * Clear all profile form fields
 */
function clearProfileForm() {
    // Clear account info
    document.getElementById('profileName').textContent = '--';
    document.getElementById('profileEmail').textContent = '--';
    document.getElementById('profileCreated').textContent = '--';
    
    // Clear address form
    document.getElementById('addressStreet').value = '';
    document.getElementById('addressCity').value = '';
    document.getElementById('addressState').value = '';
    document.getElementById('addressZip').value = '';
    document.getElementById('addressPhone').value = '';
    
    // Clear payment display
    updatePaymentDisplay(null);
    
    // Clear card form
    document.getElementById('cardNumber').value = '';
    document.getElementById('cardExpiry').value = '';
    document.getElementById('cardCvv').value = '';
    document.getElementById('cardholderName').value = '';
}

/**
 * Update the payment method display
 */
function updatePaymentDisplay(paymentMethod) {
    const displayEl = document.getElementById('paymentMethodDisplay');
    const noPaymentEl = document.getElementById('noPaymentMethod');
    const formEl = document.getElementById('addCardForm');
    
    if (paymentMethod && paymentMethod.card_number_masked) {
        // Show card display
        displayEl.classList.remove('hidden');
        noPaymentEl.classList.add('hidden');
        formEl.classList.add('hidden');
        
        // Update card details
        document.getElementById('cardNumberMasked').textContent = paymentMethod.card_number_masked;
        document.getElementById('cardType').textContent = paymentMethod.card_type;
        document.getElementById('cardExpiry').textContent = paymentMethod.expiry;
        
        // Update card icon based on type
        const iconEl = document.getElementById('cardTypeIcon');
        iconEl.textContent = getCardIcon(paymentMethod.card_type);
    } else {
        // Show no payment message
        displayEl.classList.add('hidden');
        noPaymentEl.classList.remove('hidden');
        formEl.classList.add('hidden');
    }
}

/**
 * Get card type icon
 */
function getCardIcon(cardType) {
    const icons = {
        'Visa': '💳',
        'Mastercard': '💳',
        'American Express': '💳',
        'Discover': '💳'
    };
    return icons[cardType] || '💳';
}

/**
 * Show the add card form
 */
function showAddCardForm() {
    document.getElementById('paymentMethodDisplay').classList.add('hidden');
    document.getElementById('noPaymentMethod').classList.add('hidden');
    document.getElementById('addCardForm').classList.remove('hidden');
    
    // Clear form
    document.getElementById('cardNumber').value = '';
    document.getElementById('cardExpiry').value = '';
    document.getElementById('cardCvv').value = '';
    document.getElementById('cardholderName').value = '';
}

/**
 * Hide the add card form
 */
function hideAddCardForm() {
    loadProfile(); // Refresh to show current state
}

/**
 * Save payment method
 */
async function savePaymentMethod(cardNumber, expiry, cvv, cardholderName) {
    const result = await apiPut('/profile/payment-method', {
        card_number: cardNumber,
        expiry: expiry,
        cvv: cvv,
        cardholder_name: cardholderName
    });
    
    if (result.ok) {
        showStatus(result.data.msg, 'success');
        loadProfile();
    } else {
        showStatus(result.error || 'Failed to save card', 'error');
    }
    
    return result.ok;
}

/**
 * Save address
 */
async function saveAddress(street, city, state, zipCode, phone) {
    const result = await apiPut('/profile/address', {
        street: street,
        city: city,
        state: state,
        zip_code: zipCode,
        phone: phone
    });
    
    if (result.ok) {
        showStatus(result.data.msg, 'success');
    } else {
        showStatus(result.error || 'Failed to save address', 'error');
    }
    
    return result.ok;
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    if (!dateStr) return '--';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch {
        return '--';
    }
}

/**
 * Format card number with spaces
 */
function formatCardNumber(value) {
    // Remove non-digits
    const cleaned = value.replace(/\D/g, '');
    // Add spaces every 4 digits
    const formatted = cleaned.match(/.{1,4}/g)?.join(' ') || cleaned;
    return formatted.substring(0, 19); // Max 16 digits + 3 spaces
}

/**
 * Format expiry date
 */
function formatExpiry(value) {
    // Remove non-digits
    const cleaned = value.replace(/\D/g, '');
    // Add slash after 2 digits
    if (cleaned.length >= 2) {
        return cleaned.substring(0, 2) + '/' + cleaned.substring(2, 4);
    }
    return cleaned;
}

/**
 * Initialize profile event listeners
 */
function initProfileEvents() {
    // Profile tabs
    document.querySelectorAll('.profile-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.profile-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.profile-tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab + 'Tab').classList.add('active');
        });
    });
    
    // Profile button
    document.getElementById('profileBtn')?.addEventListener('click', showProfileModal);
    
    // Card number formatting
    document.getElementById('cardNumber')?.addEventListener('input', (e) => {
        e.target.value = formatCardNumber(e.target.value);
    });
    
    // Expiry formatting
    document.getElementById('cardExpiry')?.addEventListener('input', (e) => {
        e.target.value = formatExpiry(e.target.value);
    });
    
    // Add card form submission
    document.getElementById('addCardForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const cardNumber = document.getElementById('cardNumber').value;
        const expiry = document.getElementById('cardExpiry').value;
        const cvv = document.getElementById('cardCvv').value;
        const name = document.getElementById('cardholderName').value;
        
        await savePaymentMethod(cardNumber, expiry, cvv, name);
    });
    
    // Address form submission
    document.getElementById('addressForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const street = document.getElementById('addressStreet').value;
        const city = document.getElementById('addressCity').value;
        const state = document.getElementById('addressState').value;
        const zip = document.getElementById('addressZip').value;
        const phone = document.getElementById('addressPhone').value;
        
        await saveAddress(street, city, state, zip, phone);
    });
    
    // Close modal on background click
    document.getElementById('profileModal')?.addEventListener('click', (e) => {
        if (e.target.id === 'profileModal') {
            hideProfileModal();
        }
    });
}

