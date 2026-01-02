/**
 * Frontend Validation Utilities
 * Client-side validation for coordinates and other inputs
 */

// US Geographic Bounds
const US_BOUNDS = {
    continental: {
        latMin: 24.396308,
        latMax: 49.384358,
        lngMin: -125.0,
        lngMax: -66.93457
    },
    hawaii: {
        latMin: 18.5,
        latMax: 22.5,
        lngMin: -160.5,
        lngMax: -154.5
    },
    alaska: {
        latMin: 51.0,
        latMax: 71.5,
        lngMin: -180.0,
        lngMax: -129.0
    },
    puertoRico: {
        latMin: 17.5,
        latMax: 18.6,
        lngMin: -68.0,
        lngMax: -64.5
    }
};

/**
 * Validate coordinate values
 * @param {string|number} lat - Latitude value
 * @param {string|number} lng - Longitude value
 * @param {Object} options - Validation options
 * @returns {Object} { valid: boolean, lat: number, lng: number, error: string, suggestions: string[] }
 */
function validateCoordinates(lat, lng, options = {}) {
    const { checkUSBounds = false, allowNullIsland = false } = options;
    const result = { valid: false, lat: null, lng: null, error: null, suggestions: [] };
    
    // Check for empty values
    if (lat === null || lat === undefined || lat === '') {
        result.error = 'Latitude is required';
        result.suggestions.push('Enter a latitude value (e.g., 30.2672 for Austin, TX)');
        return result;
    }
    
    if (lng === null || lng === undefined || lng === '') {
        result.error = 'Longitude is required';
        result.suggestions.push('Enter a longitude value (e.g., -97.7431 for Austin, TX)');
        return result;
    }
    
    // Convert to numbers
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);
    
    // Check if valid numbers
    if (isNaN(latNum)) {
        result.error = 'Latitude must be a valid number';
        result.suggestions.push('Remove any letters or special characters from latitude');
        return result;
    }
    
    if (isNaN(lngNum)) {
        result.error = 'Longitude must be a valid number';
        result.suggestions.push('Remove any letters or special characters from longitude');
        return result;
    }
    
    // Check for Infinity
    if (!isFinite(latNum) || !isFinite(lngNum)) {
        result.error = 'Coordinates must be finite numbers';
        return result;
    }
    
    // Range validation
    if (latNum < -90 || latNum > 90) {
        result.error = `Latitude must be between -90 and 90 (got ${latNum})`;
        if (lngNum >= -90 && lngNum <= 90 && (latNum >= -180 && latNum <= 180)) {
            result.suggestions.push('Latitude and longitude may be swapped. Try switching them.');
        }
        return result;
    }
    
    if (lngNum < -180 || lngNum > 180) {
        result.error = `Longitude must be between -180 and 180 (got ${lngNum})`;
        return result;
    }
    
    // Null Island check
    if (!allowNullIsland && latNum === 0 && lngNum === 0) {
        result.error = 'Coordinates (0, 0) is "Null Island" - not a valid location';
        result.suggestions.push('Enter the actual coordinates for your location');
        return result;
    }
    
    // Check for positive longitude in US (common mistake)
    if (lngNum > 0 && lngNum >= 66 && lngNum <= 125) {
        result.error = `US longitudes are negative. Did you mean -${lngNum}?`;
        result.suggestions.push(`Try using -${lngNum} for the longitude`);
        return result;
    }
    
    // US bounds check (optional)
    if (checkUSBounds) {
        const inUS = isInUSBounds(latNum, lngNum);
        if (!inUS) {
            result.error = `Location (${latNum.toFixed(4)}, ${lngNum.toFixed(4)}) appears to be outside US territory`;
            result.suggestions.push('Verify the coordinates are correct');
            result.suggestions.push('Scooters can only be placed within US locations');
            return result;
        }
    }
    
    // Valid!
    result.valid = true;
    result.lat = Math.round(latNum * 1000000) / 1000000;  // 6 decimal precision
    result.lng = Math.round(lngNum * 1000000) / 1000000;
    return result;
}

/**
 * Check if coordinates are within US territory
 */
function isInUSBounds(lat, lng) {
    // Continental US
    if (lat >= US_BOUNDS.continental.latMin && lat <= US_BOUNDS.continental.latMax &&
        lng >= US_BOUNDS.continental.lngMin && lng <= US_BOUNDS.continental.lngMax) {
        return true;
    }
    
    // Hawaii
    if (lat >= US_BOUNDS.hawaii.latMin && lat <= US_BOUNDS.hawaii.latMax &&
        lng >= US_BOUNDS.hawaii.lngMin && lng <= US_BOUNDS.hawaii.lngMax) {
        return true;
    }
    
    // Alaska (main)
    if (lat >= US_BOUNDS.alaska.latMin && lat <= US_BOUNDS.alaska.latMax &&
        lng >= US_BOUNDS.alaska.lngMin && lng <= US_BOUNDS.alaska.lngMax) {
        return true;
    }
    
    // Puerto Rico
    if (lat >= US_BOUNDS.puertoRico.latMin && lat <= US_BOUNDS.puertoRico.latMax &&
        lng >= US_BOUNDS.puertoRico.lngMin && lng <= US_BOUNDS.puertoRico.lngMax) {
        return true;
    }
    
    return false;
}

/**
 * Format coordinates for display
 */
function formatCoordinates(lat, lng, precision = 4) {
    if (lat === null || lng === null) return 'Unknown location';
    return `${parseFloat(lat).toFixed(precision)}, ${parseFloat(lng).toFixed(precision)}`;
}

/**
 * Validate a radius value
 */
function validateRadius(radius, maxRadius = 50000) {
    const result = { valid: false, radius: null, error: null };
    
    if (radius === null || radius === undefined || radius === '') {
        result.error = 'Radius is required';
        return result;
    }
    
    const radiusNum = parseFloat(radius);
    
    if (isNaN(radiusNum)) {
        result.error = 'Radius must be a valid number';
        return result;
    }
    
    if (radiusNum <= 0) {
        result.error = 'Radius must be greater than 0';
        return result;
    }
    
    if (radiusNum > maxRadius) {
        result.error = `Radius cannot exceed ${maxRadius} meters (${(maxRadius/1000).toFixed(1)} km)`;
        return result;
    }
    
    result.valid = true;
    result.radius = radiusNum;
    return result;
}

/**
 * Show validation error with visual feedback
 */
function showValidationError(inputElement, message, suggestions = []) {
    // Add error styling
    inputElement.classList.add('validation-error');
    inputElement.classList.remove('validation-success');
    
    // Find or create error message element
    let errorEl = inputElement.parentElement.querySelector('.validation-message');
    if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.className = 'validation-message';
        inputElement.parentElement.appendChild(errorEl);
    }
    
    let html = `<span class="error-text">❌ ${message}</span>`;
    if (suggestions.length > 0) {
        html += '<ul class="suggestions">';
        suggestions.forEach(s => html += `<li>💡 ${s}</li>`);
        html += '</ul>';
    }
    
    errorEl.innerHTML = html;
    errorEl.style.display = 'block';
}

/**
 * Clear validation error
 */
function clearValidationError(inputElement) {
    inputElement.classList.remove('validation-error');
    inputElement.classList.add('validation-success');
    
    const errorEl = inputElement.parentElement.querySelector('.validation-message');
    if (errorEl) {
        errorEl.style.display = 'none';
    }
}

/**
 * Clear all validation styling
 */
function clearValidation(inputElement) {
    inputElement.classList.remove('validation-error', 'validation-success');
    
    const errorEl = inputElement.parentElement.querySelector('.validation-message');
    if (errorEl) {
        errorEl.style.display = 'none';
    }
}

// Export for use in other modules
window.validateCoordinates = validateCoordinates;
window.validateRadius = validateRadius;
window.isInUSBounds = isInUSBounds;
window.formatCoordinates = formatCoordinates;
window.showValidationError = showValidationError;
window.clearValidationError = clearValidationError;
window.clearValidation = clearValidation;

