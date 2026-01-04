/**
 * SCORPION AI - Client Portal JavaScript
 * Authentication and common functions for client portal
 */

// Check authentication on page load
function checkAuth() {
    const client = JSON.parse(sessionStorage.getItem('client') || 'null');
    if (!client) {
        window.location.href = 'login.html';
        return null;
    }
    return client;
}

// Logout function
function logout() {
    sessionStorage.removeItem('client');
    window.location.href = 'login.html';
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0
    }).format(amount);
}

// Format date
function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

// API base URL
const API_BASE = '/api';

// Fetch wrapper with error handling
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

// Load client data
async function loadClientData(clientId) {
    try {
        const data = await fetchAPI(`/clients/${clientId}`);
        return data;
    } catch (e) {
        // Return demo data
        return {
            id: clientId,
            name: 'Demo Client',
            tier: 'pro',
            months_paid: 6,
            monthly_rate: 200,
            baby_assigned: 'VULCAN',
            ownership_percent: 50,
            remaining_balance: 1200
        };
    }
}

// Load projects
async function loadProjects(clientId) {
    try {
        const data = await fetchAPI(`/clients/${clientId}/projects`);
        return data.projects;
    } catch (e) {
        // Return demo data
        return [
            {
                name: 'AI Lead Qualification',
                status: 'active',
                progress: 75,
                start_date: '2024-01-20',
                due_date: '2024-03-20'
            }
        ];
    }
}

// Export functions
window.checkAuth = checkAuth;
window.logout = logout;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.fetchAPI = fetchAPI;
window.loadClientData = loadClientData;
window.loadProjects = loadProjects;

console.log('🦂 SCORPION AI Client Portal loaded');
