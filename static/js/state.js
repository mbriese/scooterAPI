/**
 * State Module - Centralized application state
 */

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

