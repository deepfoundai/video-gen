// Real AWS Cognito authentication
import { CognitoUserPool, CognitoUser, AuthenticationDetails, CognitoRefreshToken } from 'amazon-cognito-identity-js';

// Cognito configuration
const poolData = {
    UserPoolId: 'us-east-1_q9cVE7WTT',
    ClientId: '7paapnr8fbkanimk5bgpriagmg'
};

const userPool = new CognitoUserPool(poolData);

// Utility to decode JWT and get expiration
function getTokenExp(token) {
    try {
        const [, payloadB64] = token.split('.');
        const json = atob(payloadB64.replace(/-/g, '+').replace(/_/g, '/'));
        const { exp } = JSON.parse(json);
        return exp ? exp * 1000 : 0; // Convert to milliseconds
    } catch {
        return 0;
    }
}

export class Auth {
    constructor() {
        this.currentUser = null;
        this.accessToken = null;
    }

    // Authenticate user with email/password
    async signIn(email, password) {
        return new Promise((resolve, reject) => {
            const authenticationDetails = new AuthenticationDetails({
                Username: email,
                Password: password
            });

            const cognitoUser = new CognitoUser({
                Username: email,
                Pool: userPool
            });

            cognitoUser.authenticateUser(authenticationDetails, {
                onSuccess: (result) => {
                    this.currentUser = cognitoUser;
                    this.accessToken = result.getAccessToken().getJwtToken();
                    
                    // Store tokens
                    localStorage.setItem('access_token', this.accessToken);
                    localStorage.setItem('id_token', result.getIdToken().getJwtToken());
                    localStorage.setItem('refresh_token', result.getRefreshToken().getToken());
                    
                    // Emit auth ready event
                    window.dispatchEvent(new CustomEvent('authReady', { 
                        detail: { 
                            user: cognitoUser,
                            accessToken: this.accessToken 
                        } 
                    }));
                    
                    resolve({
                        accessToken: this.accessToken,
                        user: cognitoUser
                    });
                },
                onFailure: (err) => {
                    reject(err);
                }
            });
        });
    }

    // Get current access token
    getAccessToken() {
        return localStorage.getItem('access_token') || this.accessToken;
    }

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getAccessToken();
    }

    // Sign out
    signOut() {
        if (this.currentUser) {
            this.currentUser.signOut();
        }
        
        // Clear stored tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('id_token');
        localStorage.removeItem('refresh_token');
        
        this.currentUser = null;
        this.accessToken = null;
        
        // Emit auth cleared event
        window.dispatchEvent(new CustomEvent('authCleared'));
    }

    // Get current user from session
    getCurrentUser() {
        const currentUser = userPool.getCurrentUser();
        
        if (currentUser) {
            return new Promise((resolve, reject) => {
                currentUser.getSession((err, session) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    
                    if (session.isValid()) {
                        this.currentUser = currentUser;
                        this.accessToken = session.getAccessToken().getJwtToken();
                        
                        // Update stored tokens
                        localStorage.setItem('access_token', this.accessToken);
                        
                        resolve({
                            accessToken: this.accessToken,
                            user: currentUser
                        });
                    } else {
                        reject(new Error('Session invalid'));
                    }
                });
            });
        }
        
        return Promise.reject(new Error('No current user'));
    }

    // Refresh tokens using refresh token
    async refreshTokens() {
        const refreshToken = localStorage.getItem('refresh_token');
        const user = userPool.getCurrentUser();
        
        if (!refreshToken || !user) {
            throw new Error('Missing refresh token or user');
        }

        return new Promise((resolve, reject) => {
            user.refreshSession(
                new CognitoRefreshToken({ RefreshToken: refreshToken }),
                (err, session) => {
                    if (err) {
                        return reject(err);
                    }
                    
                    // Update stored tokens
                    localStorage.setItem('access_token', session.getAccessToken().getJwtToken());
                    localStorage.setItem('id_token', session.getIdToken().getJwtToken());
                    
                    // Update refresh token if rotated
                    const newRefreshToken = session.getRefreshToken();
                    if (newRefreshToken) {
                        localStorage.setItem('refresh_token', newRefreshToken.getToken());
                    }
                    
                    // Update instance variables
                    this.accessToken = session.getAccessToken().getJwtToken();
                    
                    resolve();
                }
            );
        });
    }

    // Get valid ID token (with auto-refresh)
    async getValidIdToken() {
        const idToken = localStorage.getItem('id_token');
        if (!idToken) {
            throw new Error('No ID token available');
        }
        
        const exp = getTokenExp(idToken);
        const fiveMinutes = 5 * 60 * 1000;
        
        // If token is still fresh (expires in more than 5 minutes), return it
        if (Date.now() < exp - fiveMinutes) {
            return idToken;
        }
        
        // Token expires soon, refresh it
        try {
            await this.refreshTokens();
            return localStorage.getItem('id_token');
        } catch (error) {
            // Refresh failed, return current token and let API call handle the error
            console.error('Token refresh failed:', error);
            return idToken;
        }
    }
}

// Global auth instance
export const auth = new Auth();