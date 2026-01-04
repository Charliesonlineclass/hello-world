/**
 * SCORPION AI - Admin Dashboard JavaScript
 * Pandora's Castle Admin Functions
 */

const API_BASE = '/api';

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function formatTime(dateStr) {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// API Functions
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
        console.error(`API Error: ${endpoint}`, error);
        return null;
    }
}

// Dashboard Data
async function refreshData() {
    updateLastUpdated();

    // Try to fetch from API, fallback to demo data
    let dashboard;
    try {
        dashboard = await fetchAPI('/admin/dashboard');
    } catch (e) {
        // Demo data
        dashboard = {
            overview: {
                total_leads: 12,
                active_clients: 3,
                total_revenue: 8200,
                active_projects: 5
            },
            leads: {
                total: 12,
                by_status: { new: 3, contacted: 4, qualified: 2, proposal: 2, won: 1 },
                conversion_rate: 8.3
            },
            clients: {
                by_tier: { starter: 0, pro: 1, empire: 2 }
            },
            recent_activity: [
                { client_name: 'J3 Structural', content: 'Project update meeting', timestamp: new Date().toISOString(), comm_type: 'meeting' },
                { client_name: 'IPC Solutions', content: 'Training session completed', timestamp: new Date().toISOString(), comm_type: 'call' },
                { client_name: 'Antonio M.', content: 'Payment received', timestamp: new Date().toISOString(), comm_type: 'note' }
            ],
            top_clients: [
                { name: 'Antonio Martinez', company: 'Banking Corp', tier: 'empire', balance_paid: 4500 },
                { name: 'IPC Solutions', company: 'IPC Solutions', tier: 'empire', balance_paid: 2500 },
                { name: 'J3 Structural', company: 'J3 Structural', tier: 'pro', balance_paid: 1200 }
            ]
        };
    }

    if (dashboard) {
        updateOverviewCards(dashboard.overview);
        updatePipeline(dashboard.leads?.by_status || {});
        updateConversionRate(dashboard.leads?.conversion_rate || 0);
        updateTopClients(dashboard.top_clients || []);
        updateActivityFeed(dashboard.recent_activity || []);
        updateRevenueChart();
    }
}

function updateLastUpdated() {
    const el = document.getElementById('last-updated');
    if (el) {
        el.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }
}

function updateOverviewCards(overview) {
    const elements = {
        'total-leads': overview.total_leads,
        'active-clients': overview.active_clients,
        'total-revenue': formatCurrency(overview.total_revenue),
        'active-projects': overview.active_projects
    };

    for (const [id, value] of Object.entries(elements)) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }
}

function updatePipeline(byStatus) {
    const pipeline = document.getElementById('pipeline');
    if (!pipeline) return;

    const stages = [
        { key: 'new', label: 'New', color: 'bg-gray-500' },
        { key: 'contacted', label: 'Contacted', color: 'bg-blue-500' },
        { key: 'qualified', label: 'Qualified', color: 'bg-yellow-500' },
        { key: 'proposal', label: 'Proposal', color: 'bg-purple-500' },
        { key: 'negotiation', label: 'Negotiation', color: 'bg-orange-500' },
        { key: 'won', label: 'Won', color: 'bg-green-500' },
        { key: 'lost', label: 'Lost', color: 'bg-red-500' }
    ];

    pipeline.innerHTML = stages.map(stage => `
        <div class="text-center">
            <div class="text-2xl font-bold mb-2">${byStatus[stage.key] || 0}</div>
            <div class="h-2 ${stage.color} rounded-full mb-2"></div>
            <div class="text-xs text-gray-400">${stage.label}</div>
        </div>
    `).join('');
}

function updateConversionRate(rate) {
    const rateEl = document.getElementById('conversion-rate');
    const circleEl = document.getElementById('conversion-circle');

    if (rateEl) rateEl.textContent = `${rate.toFixed(1)}%`;

    if (circleEl) {
        // Circle circumference is ~352 (2 * PI * 56)
        const offset = 352 - (352 * rate / 100);
        circleEl.style.strokeDashoffset = offset;
    }
}

function updateTopClients(clients) {
    const container = document.getElementById('top-clients');
    if (!container) return;

    const tierColors = {
        starter: 'bg-gray-500',
        pro: 'bg-cyan-500',
        empire: 'bg-gradient-to-r from-yellow-500 to-cyan-500'
    };

    container.innerHTML = clients.map((client, i) => `
        <div class="flex items-center justify-between p-3 bg-slate-900 rounded-xl">
            <div class="flex items-center">
                <div class="w-8 h-8 ${tierColors[client.tier] || 'bg-gray-500'} rounded-lg flex items-center justify-center text-sm font-bold mr-3">
                    ${i + 1}
                </div>
                <div>
                    <div class="font-medium">${client.name}</div>
                    <div class="text-xs text-gray-400">${client.company || ''}</div>
                </div>
            </div>
            <div class="text-right">
                <div class="font-semibold text-green-400">${formatCurrency(client.balance_paid)}</div>
                <div class="text-xs text-gray-400 capitalize">${client.tier}</div>
            </div>
        </div>
    `).join('');
}

function updateActivityFeed(activity) {
    const container = document.getElementById('activity-feed');
    if (!container) return;

    const typeIcons = {
        email: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>',
        call: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>',
        meeting: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0"/></svg>',
        chat: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>',
        note: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>'
    };

    container.innerHTML = activity.map(item => `
        <div class="flex items-start p-3 bg-slate-900 rounded-xl">
            <div class="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center mr-3 text-cyan-400">
                ${typeIcons[item.comm_type] || typeIcons.note}
            </div>
            <div class="flex-1">
                <div class="flex justify-between">
                    <span class="font-medium">${item.client_name}</span>
                    <span class="text-xs text-gray-500">${formatTime(item.timestamp)}</span>
                </div>
                <p class="text-sm text-gray-400">${item.content}</p>
            </div>
        </div>
    `).join('');
}

function updateRevenueChart() {
    const canvas = document.getElementById('revenueChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Demo data for chart
    const labels = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan'];
    const data = [800, 1200, 1500, 1800, 2000, 2200];

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue',
                data: data,
                borderColor: '#22d3ee',
                backgroundColor: 'rgba(34, 211, 238, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#22d3ee',
                pointBorderColor: '#fff',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#9ca3af'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#9ca3af',
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });
}

// Export for global use
window.refreshData = refreshData;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.fetchAPI = fetchAPI;

console.log('🦂 SCORPION AI Admin Dashboard loaded');
