/**
 * SCORPION KING Dashboard - JavaScript Application
 * =================================================
 * Handles all dashboard interactions, API calls, and real-time updates.
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

const CONFIG = {
    API_BASE: 'http://localhost:8080',
    REFRESH_INTERVAL: 30000,  // 30 seconds
    TOAST_DURATION: 5000,     // 5 seconds
};

// Baby definitions
const BABIES = {
    MARCUS: { model: 'mistral', role: 'Strategy & Analysis', color: '#4A90D9' },
    VULCAN: { model: 'codellama', role: 'Code & Technical', color: '#9B59B6' },
    HERMES: { model: 'phi', role: 'Quick Responses', color: '#2ECC71' },
    APOLLO: { model: 'llama2', role: 'Creative Writing', color: '#E67E22' },
    ATHENA: { model: 'mistral', role: 'Research & Knowledge', color: '#1ABC9C' },
};

// =============================================================================
// STATE
// =============================================================================

let state = {
    systemOnline: false,
    babies: {},
    services: {},
    stats: {
        leadsToday: 0,
        callsToday: 0,
        quotesToday: 0,
        conversionRate: 0
    },
    activities: []
};

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Make API request with error handling
 */
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Request failed: ${endpoint}`, error);
        throw error;
    }
}

/**
 * Fetch system status
 */
async function fetchStatus() {
    try {
        const data = await apiRequest('/status');
        state.systemOnline = true;
        state.services = data.services || {};
        updateSystemStatus(true);
        updateServicesGrid(data.services);
        return data;
    } catch (error) {
        state.systemOnline = false;
        updateSystemStatus(false);
        return null;
    }
}

/**
 * Fetch baby statuses
 */
async function fetchBabies() {
    try {
        const data = await apiRequest('/babies');
        state.babies = data.babies || {};
        updateBabiesGrid(data.babies);
        return data;
    } catch (error) {
        console.error('Failed to fetch babies:', error);
        return null;
    }
}

/**
 * Fetch statistics
 */
async function fetchStats() {
    try {
        const data = await apiRequest('/stats');
        state.stats = data;
        updateStatsCards(data);
        return data;
    } catch (error) {
        console.error('Failed to fetch stats:', error);
        return null;
    }
}

/**
 * Ask a baby a question
 */
async function askBaby(babyName, prompt) {
    try {
        const data = await apiRequest('/ask', {
            method: 'POST',
            body: JSON.stringify({
                baby: babyName,
                prompt: prompt
            })
        });

        addActivity(`Asked ${babyName}: "${prompt.substring(0, 50)}..."`);
        showToast(`${babyName} responded!`, 'success');
        return data;
    } catch (error) {
        showToast(`Failed to reach ${babyName}`, 'error');
        throw error;
    }
}

/**
 * Submit a new lead
 */
async function submitLead(leadData) {
    try {
        const data = await apiRequest('/leads', {
            method: 'POST',
            body: JSON.stringify(leadData)
        });

        addActivity(`New lead added: ${leadData.name}`);
        showToast('Lead added successfully!', 'success');
        state.stats.leadsToday++;
        updateStatsCards(state.stats);
        return data;
    } catch (error) {
        showToast('Failed to add lead', 'error');
        throw error;
    }
}

/**
 * Log a call
 */
async function logCall(callData) {
    try {
        const data = await apiRequest('/calls', {
            method: 'POST',
            body: JSON.stringify(callData)
        });

        addActivity(`Call logged: ${callData.caller_name}`);
        showToast('Call logged successfully!', 'success');
        state.stats.callsToday++;
        updateStatsCards(state.stats);
        return data;
    } catch (error) {
        showToast('Failed to log call', 'error');
        throw error;
    }
}

/**
 * Generate a quote
 */
async function generateQuote(quoteData) {
    try {
        const data = await apiRequest('/quotes', {
            method: 'POST',
            body: JSON.stringify(quoteData)
        });

        addActivity(`Quote generated for: ${quoteData.client_name}`);
        showToast('Quote generated!', 'success');
        state.stats.quotesToday++;
        updateStatsCards(state.stats);
        return data;
    } catch (error) {
        showToast('Failed to generate quote', 'error');
        throw error;
    }
}

// =============================================================================
// UI UPDATE FUNCTIONS
// =============================================================================

/**
 * Update system status indicator
 */
function updateSystemStatus(online) {
    const statusEl = document.getElementById('system-status');
    const dot = statusEl.querySelector('.status-dot');
    const text = statusEl.querySelector('.status-text');

    dot.className = 'status-dot ' + (online ? 'online' : 'offline');
    text.textContent = online ? 'System Online' : 'System Offline';
}

/**
 * Update stats cards
 */
function updateStatsCards(stats) {
    document.getElementById('leads-today').textContent = stats.leadsToday || 0;
    document.getElementById('calls-today').textContent = stats.callsToday || 0;
    document.getElementById('quotes-today').textContent = stats.quotesToday || 0;
    document.getElementById('conversion-rate').textContent = (stats.conversionRate || 0) + '%';
}

/**
 * Update babies grid
 */
function updateBabiesGrid(babies) {
    const grid = document.getElementById('babies-grid');
    const cards = grid.querySelectorAll('.baby-card');

    cards.forEach(card => {
        const babyName = card.dataset.baby;
        const statusEl = card.querySelector('.baby-status');
        const isOnline = babies && babies[babyName] && babies[babyName].online;

        statusEl.className = 'baby-status ' + (isOnline ? 'online' : 'offline');
    });
}

/**
 * Update services grid
 */
function updateServicesGrid(services) {
    const grid = document.getElementById('services-grid');
    const items = grid.querySelectorAll('.service-item');

    items.forEach(item => {
        const serviceName = item.dataset.service;
        const statusEl = item.querySelector('.service-status');
        const isOnline = services && services[serviceName] && services[serviceName].status === 'healthy';

        statusEl.className = 'service-status ' + (isOnline ? 'online' : 'offline');
    });
}

/**
 * Add activity to feed
 */
function addActivity(text) {
    const feed = document.getElementById('activity-feed');
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    const item = document.createElement('div');
    item.className = 'activity-item';
    item.innerHTML = `
        <span class="activity-time">${time}</span>
        <span class="activity-text">${text}</span>
    `;

    feed.insertBefore(item, feed.firstChild);

    // Keep only last 10 activities
    while (feed.children.length > 10) {
        feed.removeChild(feed.lastChild);
    }

    state.activities.unshift({ time, text });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, CONFIG.TOAST_DURATION);
}

/**
 * Update clock
 */
function updateClock() {
    const timeEl = document.getElementById('current-time');
    const now = new Date();
    timeEl.textContent = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// =============================================================================
// MODAL FUNCTIONS
// =============================================================================

/**
 * Open modal
 */
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

/**
 * Close modal
 */
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

/**
 * Close all modals
 */
function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

// =============================================================================
// EVENT HANDLERS
// =============================================================================

/**
 * Handle Ask Baby form submission
 */
async function handleAskSubmit() {
    const baby = document.getElementById('ask-baby-select').value;
    const prompt = document.getElementById('ask-prompt').value;

    if (!prompt.trim()) {
        showToast('Please enter a question', 'error');
        return;
    }

    const responseArea = document.getElementById('ask-response');
    responseArea.innerHTML = '<div class="response-placeholder">Thinking...</div>';

    try {
        const result = await askBaby(baby, prompt);
        responseArea.innerHTML = `<div class="response-text">${result.response || 'No response received'}</div>`;
    } catch (error) {
        responseArea.innerHTML = `<div class="response-error">Error: Could not reach ${baby}</div>`;
    }
}

/**
 * Handle Lead form submission
 */
async function handleLeadSubmit() {
    const data = {
        name: document.getElementById('lead-name').value,
        email: document.getElementById('lead-email').value,
        phone: document.getElementById('lead-phone').value,
        source: document.getElementById('lead-source').value,
        notes: document.getElementById('lead-notes').value
    };

    if (!data.name.trim()) {
        showToast('Please enter a name', 'error');
        return;
    }

    try {
        await submitLead(data);
        closeModal('modal-lead');
        // Reset form
        document.getElementById('lead-name').value = '';
        document.getElementById('lead-email').value = '';
        document.getElementById('lead-phone').value = '';
        document.getElementById('lead-notes').value = '';
    } catch (error) {
        // Error handled in submitLead
    }
}

/**
 * Handle Call form submission
 */
async function handleCallSubmit() {
    const data = {
        caller_name: document.getElementById('call-name').value,
        caller_phone: document.getElementById('call-phone').value,
        duration: parseInt(document.getElementById('call-duration').value),
        summary: document.getElementById('call-summary').value,
        outcome: document.getElementById('call-outcome').value
    };

    if (!data.caller_name.trim()) {
        showToast('Please enter caller name', 'error');
        return;
    }

    try {
        await logCall(data);
        closeModal('modal-call');
        // Reset form
        document.getElementById('call-name').value = '';
        document.getElementById('call-phone').value = '';
        document.getElementById('call-duration').value = '5';
        document.getElementById('call-summary').value = '';
    } catch (error) {
        // Error handled in logCall
    }
}

/**
 * Handle Quote form submission
 */
async function handleQuoteSubmit() {
    const data = {
        client_name: document.getElementById('quote-client').value,
        project_type: document.getElementById('quote-type').value,
        project_details: document.getElementById('quote-details').value,
        urgency: document.getElementById('quote-urgency').value
    };

    if (!data.client_name.trim()) {
        showToast('Please enter client name', 'error');
        return;
    }

    try {
        await generateQuote(data);
        closeModal('modal-quote');
        // Reset form
        document.getElementById('quote-client').value = '';
        document.getElementById('quote-details').value = '';
    } catch (error) {
        // Error handled in generateQuote
    }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

/**
 * Initialize dashboard
 */
function init() {
    // Update clock every second
    updateClock();
    setInterval(updateClock, 1000);

    // Initial data fetch
    fetchStatus();
    fetchBabies();
    fetchStats();

    // Auto-refresh
    setInterval(() => {
        fetchStatus();
        fetchBabies();
        fetchStats();
    }, CONFIG.REFRESH_INTERVAL);

    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            // Future: Switch sections based on data-section
        });
    });

    // Quick action buttons
    document.getElementById('action-ask').addEventListener('click', () => openModal('modal-ask'));
    document.getElementById('action-lead').addEventListener('click', () => openModal('modal-lead'));
    document.getElementById('action-call').addEventListener('click', () => openModal('modal-call'));
    document.getElementById('action-quote').addEventListener('click', () => openModal('modal-quote'));

    // Modal close buttons
    document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
        btn.addEventListener('click', closeAllModals);
    });

    // Close modal on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeAllModals();
        });
    });

    // Form submissions
    document.getElementById('ask-submit').addEventListener('click', handleAskSubmit);
    document.getElementById('lead-submit').addEventListener('click', handleLeadSubmit);
    document.getElementById('call-submit').addEventListener('click', handleCallSubmit);
    document.getElementById('quote-submit').addEventListener('click', handleQuoteSubmit);

    // Refresh babies button
    document.getElementById('refresh-babies').addEventListener('click', () => {
        fetchBabies();
        showToast('Refreshing baby status...', 'info');
    });

    // Shutdown button
    document.getElementById('shutdown-btn').addEventListener('click', () => {
        if (confirm('Are you sure you want to shutdown SCORPION?')) {
            showToast('Initiating shutdown...', 'error');
            // apiRequest('/shutdown', { method: 'POST' });
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeAllModals();
    });

    // Add initial activity
    addActivity('Dashboard initialized');

    console.log('🦂 SCORPION Dashboard initialized');
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);
