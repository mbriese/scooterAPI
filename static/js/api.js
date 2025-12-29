/**
 * API Module - Centralized API call wrapper
 * Provides consistent error handling and response parsing
 */

const API_BASE = window.location.origin;
const NOMINATIM_API = 'https://nominatim.openstreetmap.org';

/**
 * Make an API call with consistent error handling
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {Object} options - Fetch options
 * @returns {Promise<{ok: boolean, data: any, error: string|null}>}
 */
async function apiCall(endpoint, options = {}) {
    const defaultOptions = {
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    // Don't set Content-Type for GET requests without body
    if (!options.body && mergedOptions.method !== 'POST' && mergedOptions.method !== 'PUT') {
        delete mergedOptions.headers['Content-Type'];
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, mergedOptions);
        const data = await response.json();
        
        return {
            ok: response.ok,
            status: response.status,
            data: data,
            error: response.ok ? null : (data.msg || 'Request failed')
        };
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        return {
            ok: false,
            status: 0,
            data: null,
            error: 'Connection error. Please try again.'
        };
    }
}

/**
 * GET request helper
 */
async function apiGet(endpoint) {
    return apiCall(endpoint, { method: 'GET' });
}

/**
 * POST request helper
 */
async function apiPost(endpoint, body) {
    return apiCall(endpoint, {
        method: 'POST',
        body: JSON.stringify(body)
    });
}

/**
 * PUT request helper
 */
async function apiPut(endpoint, body) {
    return apiCall(endpoint, {
        method: 'PUT',
        body: JSON.stringify(body)
    });
}

/**
 * DELETE request helper
 */
async function apiDelete(endpoint) {
    return apiCall(endpoint, { method: 'DELETE' });
}

/**
 * Geocode an address using Nominatim
 */
async function geocodeAddress(query) {
    if (!query || query.length < 3) return [];
    
    try {
        const response = await fetch(
            `${NOMINATIM_API}/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`,
            { headers: { 'Accept-Language': 'en' } }
        );
        
        if (!response.ok) throw new Error('Geocoding failed');
        return await response.json();
    } catch (error) {
        console.error('Geocoding error:', error);
        return [];
    }
}

