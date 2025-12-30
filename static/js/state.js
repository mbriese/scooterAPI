/**
 * State Module - Centralized application state
 */

/**
 * Shared city data - single source of truth for all city references
 * Used by: admin.js (move/add scooters), map.js (city markers), main.js (add scooter form)
 */
const CITIES = {
    // 🇺🇸 United States
    'New York City, NY': { lat: 40.7128, lng: -74.0060, region: 'US', shortName: 'New York City' },
    'Los Angeles, CA': { lat: 34.0522, lng: -118.2437, region: 'US', shortName: 'Los Angeles' },
    'Chicago, IL': { lat: 41.8781, lng: -87.6298, region: 'US', shortName: 'Chicago' },
    'Houston, TX': { lat: 29.7604, lng: -95.3698, region: 'US', shortName: 'Houston' },
    'Phoenix, AZ': { lat: 33.4484, lng: -112.0740, region: 'US', shortName: 'Phoenix' },
    'San Francisco, CA': { lat: 37.7749, lng: -122.4194, region: 'US', shortName: 'San Francisco' },
    'Seattle, WA': { lat: 47.6062, lng: -122.3321, region: 'US', shortName: 'Seattle' },
    'Miami, FL': { lat: 25.7617, lng: -80.1918, region: 'US', shortName: 'Miami' },
    'Denver, CO': { lat: 39.7392, lng: -104.9903, region: 'US', shortName: 'Denver' },
    'Austin, TX': { lat: 30.2672, lng: -97.7431, region: 'US', shortName: 'Austin' },
    // 🇪🇺 Europe
    'London, UK': { lat: 51.5074, lng: -0.1278, region: 'EU', shortName: 'London' },
    'Paris, France': { lat: 48.8566, lng: 2.3522, region: 'EU', shortName: 'Paris' },
    'Berlin, Germany': { lat: 52.5200, lng: 13.4050, region: 'EU', shortName: 'Berlin' },
    'Rome, Italy': { lat: 41.9028, lng: 12.4964, region: 'EU', shortName: 'Rome' },
    'Amsterdam, Netherlands': { lat: 52.3676, lng: 4.9041, region: 'EU', shortName: 'Amsterdam' },
    'Madrid, Spain': { lat: 40.4168, lng: -3.7038, region: 'EU', shortName: 'Madrid' },
    // 🌏 Asia Pacific
    'Tokyo, Japan': { lat: 35.6762, lng: 139.6503, region: 'APAC', shortName: 'Tokyo' },
    'Hong Kong': { lat: 22.3193, lng: 114.1694, region: 'APAC', shortName: 'Hong Kong' },
    'Singapore': { lat: 1.3521, lng: 103.8198, region: 'APAC', shortName: 'Singapore' },
    'Sydney, Australia': { lat: -33.8688, lng: 151.2093, region: 'APAC', shortName: 'Sydney' }
};

/**
 * Get city coordinates by name
 */
function getCityCoords(cityName) {
    return CITIES[cityName] || null;
}

/**
 * Get all cities grouped by region
 */
function getCitiesByRegion() {
    const grouped = { US: [], EU: [], APAC: [] };
    Object.entries(CITIES).forEach(([name, data]) => {
        grouped[data.region].push({ name, ...data });
    });
    return grouped;
}

const AppState = {
    currentUser: null,
    map: null,
    markers: [],
    searchRadius: 1000,
    addressSearchTimeout: null,
    clickSearchMarker: null
};

// Getters
function getCurrentUser() {
    return AppState.currentUser;
}

function getMap() {
    return AppState.map;
}

function getMarkers() {
    return AppState.markers;
}

function getSearchRadius() {
    return AppState.searchRadius;
}

// Setters
function setCurrentUser(user) {
    AppState.currentUser = user;
}

function setMap(map) {
    AppState.map = map;
}

function setMarkers(markers) {
    AppState.markers = markers;
}

function addMarker(marker) {
    AppState.markers.push(marker);
}

function setSearchRadius(radius) {
    AppState.searchRadius = radius;
}

function setAddressSearchTimeout(timeout) {
    AppState.addressSearchTimeout = timeout;
}

function getAddressSearchTimeout() {
    return AppState.addressSearchTimeout;
}

function setClickSearchMarker(marker) {
    AppState.clickSearchMarker = marker;
}

function getClickSearchMarker() {
    return AppState.clickSearchMarker;
}

// User helpers
function isLoggedIn() {
    return AppState.currentUser !== null;
}

function isAdmin() {
    return AppState.currentUser?.role === 'admin';
}

