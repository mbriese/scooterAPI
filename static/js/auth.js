/**
 * Auth Module - Authentication functions
 */

/**
 * Check if user is logged in on page load
 */
async function checkAuthStatus() {
    const result = await apiGet('/auth/me');
    
    if (result.ok) {
        setCurrentUser(result.data.user);
        updateUIForLoggedInUser();
    } else {
        setCurrentUser(null);
        updateUIForLoggedOutUser();
    }
}

/**
 * Login with email and password
 */
async function login(email, password) {
    const result = await apiPost('/auth/login', { email, password });
    
    if (result.ok) {
        setCurrentUser(result.data.user);
        hideAuthModal();
        updateUIForLoggedInUser();
        showStatus(`Welcome back, ${result.data.user.name}!`, 'success');
        return { success: true };
    } else {
        return { success: false, error: result.error };
    }
}

/**
 * Register a new user
 */
async function register(name, email, password) {
    const result = await apiPost('/auth/register', { name, email, password });
    
    if (result.ok) {
        setCurrentUser(result.data.user);
        hideAuthModal();
        updateUIForLoggedInUser();
        showStatus(`Welcome, ${result.data.user.name}! Your account has been created.`, 'success');
        return { success: true };
    } else {
        return { success: false, error: result.error };
    }
}

/**
 * Logout current user
 */
async function logout() {
    await apiPost('/auth/logout', {});
    
    setCurrentUser(null);
    updateUIForLoggedOutUser();
    showStatus('You have been logged out.', 'info');
}

