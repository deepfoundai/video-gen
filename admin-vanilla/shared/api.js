// Shared API Utilities for Admin Dashboard
// Raw approach - shows all API operations in detail

const API_ENDPOINTS = {
    JOBS: 'https://l3erksseb4.execute-api.us-east-1.amazonaws.com/prod/v1',
    CREDITS: 'https://dbmr3la6d3.execute-api.us-east-1.amazonaws.com',
    FRONTEND: 'https://video.deepfoundai.com'
};

// Use getValidAccessToken from auth.js if available, otherwise create fallback
if (!window.getValidAccessToken) {
    window.getValidAccessToken = async () => {
        // Fallback to getting the token from auth module
        if (window.getAuthToken) {
            return window.getAuthToken();
        }
        throw new Error('Auth module not loaded');
    };
}

// Generic API call with full logging
async function apiCall(url, options = {}) {
    const startTime = Date.now();
    const requestId = Math.random().toString(36).substring(7);
    
    console.log(`[${requestId}] API Request:`, {
        url: url,
        method: options.method || 'GET',
        headers: options.headers,
        body: options.body
    });
    
    try {
        // Get valid auth token (with auto-refresh)
        if (!options.skipAuth) {
            try {
                const token = await getValidAccessToken();
                options.headers = options.headers || {};
                options.headers['Authorization'] = `Bearer ${token}`;
            } catch (error) {
                console.error('Failed to get valid auth token:', error);
                // Continue without auth token
            }
        }
        
        // Add content type for JSON
        if (options.body && typeof options.body === 'object') {
            options.headers = options.headers || {};
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }
        
        const response = await fetch(url, options);
        const duration = Date.now() - startTime;
        
        // Log response details
        console.log(`[${requestId}] API Response in ${duration}ms:`, {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            ok: response.ok
        });
        
        // Get response text
        const responseText = await response.text();
        console.log(`[${requestId}] Response body:`, responseText);
        
        // Try to parse as JSON
        let responseData;
        try {
            responseData = JSON.parse(responseText);
        } catch (e) {
            console.log(`[${requestId}] Response is not JSON:`, responseText);
            responseData = responseText;
        }
        
        // Return full details
        return {
            ok: response.ok,
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            data: responseData,
            duration: duration,
            requestId: requestId
        };
        
    } catch (error) {
        const duration = Date.now() - startTime;
        console.error(`[${requestId}] API Error in ${duration}ms:`, error);
        
        return {
            ok: false,
            status: 0,
            error: error.message || error,
            fullError: error,
            duration: duration,
            requestId: requestId
        };
    }
}

// Jobs API helpers - Using admin endpoints for proper user_id access
const JobsAPI = {
    async listJobs(limit = 100) {
        // Use admin endpoint to get user_id field
        return apiCall(`${API_ENDPOINTS.JOBS}/admin/jobs?limit=${limit}`);
    },
    
    async getJob(jobId) {
        // Try admin endpoint first, fall back to regular endpoint
        const adminResponse = await apiCall(`${API_ENDPOINTS.JOBS}/admin/jobs/${jobId}`);
        if (adminResponse.status === 404 || adminResponse.status === 0) {
            // Admin endpoint not available, use regular endpoint
            return apiCall(`${API_ENDPOINTS.JOBS}/jobs/${jobId}`);
        }
        return adminResponse;
    },
    
    async submitJob(jobData) {
        return apiCall(`${API_ENDPOINTS.JOBS}/jobs`, {
            method: 'POST',
            body: jobData
        });
    },
    
    async getJob(jobId) {
        // Try admin endpoint first for detailed info
        const adminResponse = await apiCall(`${API_ENDPOINTS.JOBS}/admin/jobs/${jobId}`);
        if (adminResponse.status === 404 || adminResponse.status === 0) {
            // Admin endpoint not available, use regular endpoint
            return apiCall(`${API_ENDPOINTS.JOBS}/jobs/${jobId}`);
        }
        return adminResponse;
    },
    
    async getJobLogs(jobId) {
        // Try admin endpoint first, fall back to regular endpoint
        const adminResponse = await apiCall(`${API_ENDPOINTS.JOBS}/admin/jobs/${jobId}/logs`);
        if (adminResponse.status === 404 || adminResponse.status === 0) {
            // Admin endpoint not available, use regular endpoint
            return apiCall(`${API_ENDPOINTS.JOBS}/jobs/${jobId}/logs`);
        }
        return adminResponse;
    }
};

// Credits API helpers
const CreditsAPI = {
    async getBalance(userId) {
        const url = userId 
            ? `${API_ENDPOINTS.CREDITS}/credits/balance?userId=${userId}`
            : `${API_ENDPOINTS.CREDITS}/credits/balance`;
        return apiCall(url);
    },
    
    async adminGetUser(userId) {
        return apiCall(`${API_ENDPOINTS.CREDITS}/credits/admin?userId=${userId}`);
    },
    
    async adminUpdateCredits(userId, credits, operation = 'set') {
        return apiCall(`${API_ENDPOINTS.CREDITS}/credits/admin`, {
            method: 'PUT',
            body: {
                userId: userId,
                credits: credits,
                operation: operation
            }
        });
    },
    
    async consumeCredits(amount) {
        return apiCall(`${API_ENDPOINTS.CREDITS}/credits/consume`, {
            method: 'POST',
            body: { amount: amount }
        });
    }
};

// DynamoDB direct helpers (via Lambda)
const DynamoAPI = {
    async scanTable(tableName, limit = 100) {
        // This would need a Lambda endpoint that does DynamoDB scans
        console.log(`DynamoDB scan not yet implemented for table: ${tableName}`);
        return { ok: false, error: 'Not implemented' };
    }
};

// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
    return `${(ms / 60000).toFixed(2)}m`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
    });
}

// Error display helper
function displayError(error, elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    let errorHtml = '<div class="error">';
    errorHtml += `<strong>Error:</strong> ${error.error || error.message || 'Unknown error'}<br>`;
    
    if (error.status) {
        errorHtml += `<strong>Status:</strong> ${error.status} ${error.statusText || ''}<br>`;
    }
    
    if (error.code) {
        errorHtml += `<strong>Code:</strong> ${error.code}<br>`;
    }
    
    if (error.duration) {
        errorHtml += `<strong>Duration:</strong> ${formatDuration(error.duration)}<br>`;
    }
    
    if (error.fullError) {
        errorHtml += '<details><summary>Full Error Details</summary>';
        errorHtml += '<pre>' + JSON.stringify(error.fullError, null, 2) + '</pre>';
        errorHtml += '</details>';
    }
    
    errorHtml += '</div>';
    element.innerHTML = errorHtml;
}

// Success display helper
function displaySuccess(message, elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.innerHTML = `<div class="success">${message}</div>`;
}

// Loading display helper
function showLoading(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.innerHTML = `<div class="loading">${message}</div>`;
}

// Export functions to global scope
window.showLoading = showLoading;
window.displayError = displayError;
window.displaySuccess = displaySuccess;