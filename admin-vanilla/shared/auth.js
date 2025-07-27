// Shared Authentication Logic for Admin Dashboard
// Raw and detailed approach - shows all auth operations

const AUTH_CONFIG = {
    region: 'us-east-1',
    userPoolId: 'us-east-1_q9cVE7WTT',
    clientId: '7paapnr8fbkanimk5bgpriagmg'
};

// Global auth state
let cognitoUser = null;
let authToken = null;
let userDetails = null;
let refreshToken = sessionStorage.getItem('adminRefreshToken') || null;

// Initialize Cognito
function initCognito() {
    console.log('Initializing Cognito with config:', AUTH_CONFIG);
    
    const poolData = {
        UserPoolId: AUTH_CONFIG.userPoolId,
        ClientId: AUTH_CONFIG.clientId
    };
    
    const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
    console.log('Cognito UserPool initialized:', userPool);
    
    return userPool;
}

// Login function with full error details
async function adminLogin(email, password) {
    console.log(`Attempting login for: ${email}`);
    const startTime = Date.now();
    
    try {
        const authenticationData = {
            Username: email,
            Password: password
        };
        
        const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);
        const userPool = initCognito();
        
        const userData = {
            Username: email,
            Pool: userPool
        };
        
        cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
        
        return new Promise((resolve, reject) => {
            cognitoUser.authenticateUser(authenticationDetails, {
                onSuccess: (result) => {
                    const duration = Date.now() - startTime;
                    console.log(`Login successful in ${duration}ms`, result);
                    
                    authToken = result.getIdToken().getJwtToken();
                    refreshToken = result.getRefreshToken() ? result.getRefreshToken().getToken() : null;
                    
                    userDetails = {
                        userId: result.getIdToken().payload.sub,
                        email: result.getIdToken().payload.email,
                        name: result.getIdToken().payload.name,
                        tokenExpiry: new Date(result.getIdToken().payload.exp * 1000),
                        rawPayload: result.getIdToken().payload
                    };
                    
                    console.log('User details:', userDetails);
                    console.log('Token (first 50 chars):', authToken.substring(0, 50) + '...');
                    
                    // Store in sessionStorage for page refreshes
                    sessionStorage.setItem('adminAuthToken', authToken);
                    sessionStorage.setItem('adminUserDetails', JSON.stringify(userDetails));
                    if (refreshToken) {
                        sessionStorage.setItem('adminRefreshToken', refreshToken);
                    }
                    
                    resolve({
                        success: true,
                        token: authToken,
                        user: userDetails,
                        duration: duration
                    });
                },
                
                onFailure: (err) => {
                    const duration = Date.now() - startTime;
                    console.error(`Login failed in ${duration}ms:`, err);
                    
                    reject({
                        success: false,
                        error: err.message || err,
                        code: err.code,
                        name: err.name,
                        statusCode: err.statusCode,
                        duration: duration,
                        fullError: err
                    });
                },
                
                newPasswordRequired: (userAttributes, requiredAttributes) => {
                    console.log('New password required:', { userAttributes, requiredAttributes });
                    reject({
                        success: false,
                        error: 'New password required',
                        code: 'NEW_PASSWORD_REQUIRED',
                        userAttributes: userAttributes,
                        requiredAttributes: requiredAttributes
                    });
                }
            });
        });
        
    } catch (error) {
        const duration = Date.now() - startTime;
        console.error('Login exception:', error);
        throw {
            success: false,
            error: error.message || error,
            duration: duration,
            fullError: error
        };
    }
}

// Check if user is authenticated
function checkAuth() {
    // First check sessionStorage
    const storedToken = sessionStorage.getItem('adminAuthToken');
    const storedUser = sessionStorage.getItem('adminUserDetails');
    
    if (storedToken && storedUser) {
        authToken = storedToken;
        userDetails = JSON.parse(storedUser);
        
        // Check if token is expired
        const tokenExpiry = new Date(userDetails.tokenExpiry);
        const now = new Date();
        
        if (tokenExpiry > now) {
            console.log('Using stored auth token, expires:', tokenExpiry);
            return true;
        } else {
            console.log('Stored token expired at:', tokenExpiry);
            clearAuth();
            return false;
        }
    }
    
    return false;
}

// Clear authentication
function clearAuth() {
    console.log('Clearing authentication');
    cognitoUser = null;
    authToken = null;
    userDetails = null;
    refreshToken = null;
    sessionStorage.removeItem('adminAuthToken');
    sessionStorage.removeItem('adminUserDetails');
    sessionStorage.removeItem('adminRefreshToken');
}

// Logout function
function adminLogout() {
    console.log('Logging out user');
    
    if (cognitoUser) {
        cognitoUser.signOut();
    }
    
    clearAuth();
    
    // Redirect to login
    if (window.location.pathname !== '/index.html' && window.location.pathname !== '/') {
        window.location.href = '../index.html';
    }
}

// Get current auth token
function getAuthToken() {
    return authToken;
}

// Get valid access token (with auto-refresh)
async function getValidAccessToken() {
    // Check if we have a token and it's still valid
    if (authToken && userDetails) {
        const tokenExpiry = new Date(userDetails.tokenExpiry).getTime();
        const now = Date.now();
        const twoMinutes = 2 * 60 * 1000;
        
        // If token has more than 2 minutes left, return it
        if (now < tokenExpiry - twoMinutes) {
            return authToken;
        }
    }
    
    // If no refresh token, throw error
    if (!refreshToken) {
        console.error('No refresh token available');
        throw new Error('No refresh token');
    }
    
    console.log('Token expiring soon, refreshing...');
    
    try {
        // Show refresh indicator
        if (window.showSpinner) window.showSpinner('refresh');
        
        // Use Cognito SDK to refresh token
        const userPool = initCognito();
        const cognitoRefreshToken = new AmazonCognitoIdentity.CognitoRefreshToken({
            RefreshToken: refreshToken
        });
        
        // Get the current user from pool
        const userData = {
            Username: userDetails.email,
            Pool: userPool
        };
        const cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
        
        return new Promise((resolve, reject) => {
            cognitoUser.refreshSession(cognitoRefreshToken, (err, session) => {
                if (err) {
                    console.error('Failed to refresh session:', err);
                    reject(err);
                    return;
                }
                
                // Update stored tokens
                authToken = session.getIdToken().getJwtToken();
                const newRefreshToken = session.getRefreshToken().getToken();
                
                // Update user details with new expiry
                userDetails.tokenExpiry = new Date(session.getIdToken().getPayload().exp * 1000);
                
                // Store updated tokens
                sessionStorage.setItem('adminAuthToken', authToken);
                sessionStorage.setItem('adminUserDetails', JSON.stringify(userDetails));
                if (newRefreshToken && newRefreshToken !== refreshToken) {
                    refreshToken = newRefreshToken;
                    sessionStorage.setItem('adminRefreshToken', refreshToken);
                }
                
                console.log('Token refreshed successfully');
                resolve(authToken);
            });
        });
        
    } catch (error) {
        console.error('Failed to refresh token:', error);
        throw error;
    } finally {
        // Hide refresh indicator
        if (window.hideSpinner) window.hideSpinner('refresh');
    }
}

// Get current user details
function getUserDetails() {
    return userDetails;
}

// Check if user is admin (based on hardcoded list for now)
function isAdmin() {
    if (!userDetails) return false;
    
    const ADMIN_USER_IDS = [
        "f4c8e4a8-3081-70cd-43f9-ea8a7b407430",  // todd.deshane@gmail.com
        "04d8c4d8-20f1-7000-5cf5-90247ec54b3a",  // todd@theintersecto.com
        "44088418-f0d1-7016-37c9-3bbf83358bb6"   // admin.test@deepfoundai.com
    ];
    
    const isAdminUser = ADMIN_USER_IDS.includes(userDetails.userId);
    console.log(`User ${userDetails.email} (${userDetails.userId}) is admin: ${isAdminUser}`);
    
    return isAdminUser;
}

// Make functions globally available for other modules
window.getValidAccessToken = getValidAccessToken;
window.getAuthToken = getAuthToken;
window.getUserDetails = getUserDetails;
window.adminLogin = adminLogin;
window.adminLogout = adminLogout;
window.checkAuth = checkAuth;
window.isAdmin = isAdmin;

// Auto-check auth on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Auth module loaded, checking authentication status');
    
    if (checkAuth()) {
        console.log('User is authenticated:', userDetails);
        // Fire custom event
        document.dispatchEvent(new CustomEvent('authReady', { detail: { user: userDetails, token: authToken } }));
    } else {
        console.log('User is not authenticated');
        document.dispatchEvent(new CustomEvent('authRequired'));
    }
});