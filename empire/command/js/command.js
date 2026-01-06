/* ═══════════════════════════════════════════════════════════════════
   SCORPION COMMAND CENTER - MAIN JAVASCRIPT
   State management, navigation, and UI rendering
   ═══════════════════════════════════════════════════════════════════ */

// ═══════════════════════════════════════════════════════════════════
// STATE MANAGEMENT
// ═══════════════════════════════════════════════════════════════════

const state = {
    currentView: 'eyes',      // 'eyes', 'client', 'account'
    selectedClient: null,
    selectedAccount: null,
    breadcrumb: ['Home'],
    weeklyChart: null
};

// ═══════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    loadEyesView();
    setupEventListeners();
});

function setupEventListeners() {
    // Add client form submission
    const addClientForm = document.getElementById('addClientForm');
    if (addClientForm) {
        addClientForm.addEventListener('submit', handleAddClient);
    }
}

// ═══════════════════════════════════════════════════════════════════
// VIEW 1: 8 EYES - EMPIRE OVERVIEW
// ═══════════════════════════════════════════════════════════════════

function loadEyesView() {
    const grid = document.getElementById('clientsGrid');
    grid.innerHTML = '';

    DEMO_DATA.clients.forEach(client => {
        const card = createClientCard(client);
        grid.appendChild(card);
    });

    // Update bottom stats
    document.getElementById('totalMRR').textContent = `$${DEMO_DATA.totals.mrr.toLocaleString()}`;
    document.getElementById('totalLeads').textContent = DEMO_DATA.totals.leads;
    document.getElementById('avgConv').textContent = DEMO_DATA.totals.avgConv;
}

function createClientCard(client) {
    const card = document.createElement('div');
    card.className = `client-card ${client.status}`;

    if (client.status === 'empty') {
        card.innerHTML = `
            <span class="add-icon">+</span>
            <span class="add-text">Add Client</span>
        `;
        card.onclick = () => openModal('addClient');
    } else {
        card.innerHTML = `
            <div class="card-header">
                <span class="eye-icon">👁️</span>
                <span class="client-name">${client.name}</span>
            </div>
            <div class="card-stats">
                <div class="card-stat">
                    <span class="stat-icon">📞</span>
                    <span class="stat-value">${client.calls}</span> Calls
                </div>
                <div class="card-stat">
                    <span class="stat-icon">📅</span>
                    <span class="stat-value">${client.appts}</span> Appts
                </div>
                <div class="card-stat">
                    <span class="stat-icon">📈</span>
                    <span class="stat-value">${client.conv}</span> Conv
                </div>
                <div class="card-stat">
                    <span class="stat-icon">💰</span>
                    <span class="stat-value">$${client.mrr}</span>/mo
                </div>
            </div>
            <div class="card-footer">
                <div class="baby-tag">
                    🦂 ${client.baby}
                    ${client.status !== 'paused' ? '<span class="status"></span>' : ''}
                </div>
                <button class="view-btn" onclick="event.stopPropagation(); navigateToClient(${client.id})">View →</button>
            </div>
        `;
        if (client.status !== 'paused') {
            card.onclick = () => navigateToClient(client.id);
        }
    }

    return card;
}

// ═══════════════════════════════════════════════════════════════════
// VIEW 2: CLIENT ZOOM
// ═══════════════════════════════════════════════════════════════════

function loadClientView(clientId) {
    const client = DEMO_DATA.clients.find(c => c.id === clientId);
    if (!client) return;

    state.selectedClient = client;

    // Update header
    const header = document.getElementById('clientHeader');
    header.innerHTML = `
        <div class="client-header-top">
            <h2>
                👁️ ${client.name}
                <span class="industry-tag">| ${client.industry} | ${client.accounts} Accounts | $${client.mrr}/mo</span>
            </h2>
            <div class="baby-assigned">
                Baby: 🦂 ${client.baby}
            </div>
        </div>
        <div class="client-stats-row">
            <div class="client-stat">
                <span class="icon">📞</span>
                <span class="value">${client.calls}</span>
                <span class="label">Total Calls</span>
            </div>
            <div class="client-stat">
                <span class="icon">📅</span>
                <span class="value">${client.appts}</span>
                <span class="label">Appts</span>
            </div>
            <div class="client-stat">
                <span class="icon">📈</span>
                <span class="value">${client.conv}</span>
                <span class="label">Conv</span>
            </div>
            <div class="client-stat">
                <span class="icon">🏆</span>
                <span class="value">Carlos: #1</span>
                <span class="label">Top Performer</span>
            </div>
        </div>
    `;

    // Load accounts/projects
    const accountsData = getClientAccounts(clientId);
    const grid = document.getElementById('accountsGrid');
    grid.innerHTML = '';

    accountsData.data.forEach(item => {
        const card = createAccountCard(item, accountsData.type);
        grid.appendChild(card);
    });
}

function createAccountCard(item, type) {
    const card = document.createElement('div');
    card.className = 'account-card';
    card.onclick = () => navigateToAccount(item.id, item.name);

    if (type === 'accounts') {
        card.innerHTML = `
            <h4>${item.name}</h4>
            <div class="account-stats">
                <div class="account-stat">
                    <span class="label">📞 Calls</span>
                    <span class="value">${item.calls}</span>
                </div>
                <div class="account-stat">
                    <span class="label">📅 Appointments</span>
                    <span class="value">${item.appts}</span>
                </div>
                <div class="account-stat">
                    <span class="label">📈 Conversion</span>
                    <span class="value">${item.conv}</span>
                </div>
            </div>
            <button class="view-btn">View Details →</button>
        `;
    } else if (type === 'projects') {
        card.innerHTML = `
            <h4>${item.name}</h4>
            <div class="account-stats">
                <div class="account-stat">
                    <span class="label">Type</span>
                    <span class="value">${item.type}</span>
                </div>
                <div class="account-stat">
                    <span class="label">Status</span>
                    <span class="value">${item.status}</span>
                </div>
                <div class="account-stat">
                    <span class="label">Value</span>
                    <span class="value">${item.value}</span>
                </div>
            </div>
            <button class="view-btn">View Details →</button>
        `;
    } else if (type === 'jobs') {
        card.innerHTML = `
            <h4>${item.name}</h4>
            <div class="account-stats">
                <div class="account-stat">
                    <span class="label">Status</span>
                    <span class="value">${item.status}</span>
                </div>
                <div class="account-stat">
                    <span class="label">Value</span>
                    <span class="value">${item.value}</span>
                </div>
            </div>
            <button class="view-btn">View Details →</button>
        `;
    }

    return card;
}

// ═══════════════════════════════════════════════════════════════════
// VIEW 3: FULL METRICS
// ═══════════════════════════════════════════════════════════════════

function loadAccountView(accountId, accountName) {
    state.selectedAccount = { id: accountId, name: accountName };
    const details = getAccountDetails(accountId);

    // Update header
    const header = document.getElementById('accountHeader');
    header.innerHTML = `
        <h2>📊 ${accountName}</h2>
        <div class="account-meta">Full performance metrics and lead management</div>
    `;

    // Render scorecard
    renderScorecard(details.coordinators);

    // Render lead bars
    renderLeadBars(details.leadStatus);

    // Render weekly chart
    renderWeeklyChart(details.weeklyData);

    // Render call log
    renderCallLog(details.callLog);

    // Render leads table
    renderLeadsTable(details.leads);
}

function renderScorecard(coordinators) {
    const table = document.getElementById('scorecardTable');
    table.innerHTML = '';

    coordinators.forEach((coord, index) => {
        const row = document.createElement('div');
        row.className = `coordinator-row ${index === 0 ? 'top-performer' : ''} ${coord.warning ? 'warning' : ''}`;

        const rankEmoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`;
        const progressClass = coord.conv >= 20 ? 'excellent' : coord.conv >= 15 ? 'good' : coord.conv >= 10 ? 'average' : 'poor';
        const progressWidth = Math.min(coord.conv * 4, 100);

        row.innerHTML = `
            <span class="rank">${rankEmoji}</span>
            <span class="coordinator-name">${coord.name}</span>
            <span class="coordinator-stat"><span class="value">${coord.calls}</span> calls</span>
            <span class="coordinator-stat"><span class="value">${coord.appts}</span> appts</span>
            <span class="coordinator-stat"><span class="value">${coord.conv.toFixed(1)}%</span></span>
            <div class="progress-bar">
                <div class="progress-fill ${progressClass}" style="width: ${progressWidth}%"></div>
            </div>
        `;

        table.appendChild(row);
    });
}

function renderLeadBars(leadStatus) {
    const container = document.getElementById('leadBars');
    const maxValue = Math.max(...Object.values(leadStatus));

    const statusConfig = {
        red: { icon: '🔴', label: 'RED (No/Rejected)' },
        orange: { icon: '🟠', label: 'ORANGE (VM/Maybe)' },
        yellow: { icon: '🟡', label: 'YELLOW (Working)' },
        green: { icon: '🟢', label: 'GREEN (Appointed)' },
        blue: { icon: '🔵', label: 'BLUE (Follow-up)' }
    };

    container.innerHTML = '';

    Object.entries(leadStatus).forEach(([status, count]) => {
        const config = statusConfig[status];
        const width = (count / maxValue) * 100;

        container.innerHTML += `
            <div class="lead-bar-row">
                <span class="lead-status-icon">${config.icon} ${config.label.split(' ')[0]}</span>
                <div class="lead-bar">
                    <div class="lead-bar-fill ${status}" style="width: ${width}%"></div>
                </div>
                <span class="lead-count">${count}</span>
            </div>
        `;
    });
}

function renderWeeklyChart(weeklyData) {
    const ctx = document.getElementById('weeklyChart').getContext('2d');

    // Destroy existing chart if any
    if (state.weeklyChart) {
        state.weeklyChart.destroy();
    }

    state.weeklyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: weeklyData.labels,
            datasets: [
                {
                    label: 'Calls',
                    data: weeklyData.calls,
                    backgroundColor: 'rgba(0, 212, 255, 0.7)',
                    borderColor: '#00d4ff',
                    borderWidth: 2,
                    borderRadius: 4
                },
                {
                    label: 'Appointments',
                    data: weeklyData.appts,
                    backgroundColor: 'rgba(255, 215, 0, 0.7)',
                    borderColor: '#ffd700',
                    borderWidth: 2,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#8a8a9a' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#8a8a9a' }
                }
            }
        }
    });
}

function renderCallLog(callLog) {
    const tbody = document.getElementById('callLogBody');
    tbody.innerHTML = '';

    callLog.forEach(call => {
        const resultClass = call.result === 'Appointment Set' ? 'green' :
                           call.result === 'Callback' ? 'yellow' :
                           call.result === 'Voicemail' ? 'orange' : 'red';

        tbody.innerHTML += `
            <tr>
                <td>${call.time}</td>
                <td>${call.coordinator}</td>
                <td>${call.lead}</td>
                <td>${call.duration}</td>
                <td><span class="status-badge ${resultClass}"></span> ${call.result}</td>
            </tr>
        `;
    });
}

function renderLeadsTable(leads) {
    const tbody = document.getElementById('leadsTableBody');
    tbody.innerHTML = '';

    leads.forEach(lead => {
        tbody.innerHTML += `
            <tr onclick="openLeadDetail(${lead.id})">
                <td><span class="status-badge ${lead.status}"></span></td>
                <td>${lead.name}</td>
                <td>${lead.phone}</td>
                <td>${lead.coordinator}</td>
                <td>${lead.lastContact}</td>
                <td>${lead.notes}</td>
                <td>
                    <button class="action-btn" onclick="event.stopPropagation(); editLead(${lead.id})">Edit</button>
                </td>
            </tr>
        `;
    });
}

// ═══════════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════════

function navigateTo(view, id = null) {
    // Hide all views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

    // Show target view
    state.currentView = view;

    switch(view) {
        case 'eyes':
            document.getElementById('viewEyes').classList.add('active');
            state.breadcrumb = ['Home'];
            state.selectedClient = null;
            state.selectedAccount = null;
            break;
        case 'client':
            document.getElementById('viewClient').classList.add('active');
            loadClientView(id);
            state.breadcrumb = ['Home', state.selectedClient.name];
            break;
        case 'account':
            document.getElementById('viewAccount').classList.add('active');
            state.breadcrumb = ['Home', state.selectedClient.name, state.selectedAccount.name];
            break;
    }

    updateBreadcrumb();
}

function navigateToClient(clientId) {
    const client = DEMO_DATA.clients.find(c => c.id === clientId);
    if (client && client.status !== 'empty') {
        state.selectedClient = client;
        navigateTo('client', clientId);
    }
}

function navigateToAccount(accountId, accountName) {
    state.selectedAccount = { id: accountId, name: accountName };
    loadAccountView(accountId, accountName);
    navigateTo('account');
}

function updateBreadcrumb() {
    const breadcrumb = document.getElementById('breadcrumb');
    breadcrumb.innerHTML = '';

    state.breadcrumb.forEach((crumb, index) => {
        const span = document.createElement('span');
        span.className = `crumb ${index === state.breadcrumb.length - 1 ? 'active' : ''}`;
        span.textContent = crumb;

        if (index === 0) {
            span.onclick = () => navigateTo('eyes');
        } else if (index === 1 && state.selectedClient) {
            span.onclick = () => navigateTo('client', state.selectedClient.id);
        }

        breadcrumb.appendChild(span);
    });
}

// ═══════════════════════════════════════════════════════════════════
// SIDEBAR
// ═══════════════════════════════════════════════════════════════════

function toggleSidebar() {
    const sidebar = document.getElementById('babiesSidebar');
    sidebar.classList.toggle('collapsed');
}

// ═══════════════════════════════════════════════════════════════════
// MODALS
// ═══════════════════════════════════════════════════════════════════

function openModal(modalType) {
    document.getElementById('modalOverlay').classList.add('active');

    // Hide all modals first
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));

    // Show specific modal
    switch(modalType) {
        case 'babyChat':
            document.getElementById('babyChatModal').classList.add('active');
            break;
        case 'leads':
            document.getElementById('leadsModal').classList.add('active');
            renderLeadsTable(DEMO_DATA.leads);
            break;
        case 'import':
            document.getElementById('importModal').classList.add('active');
            break;
        case 'addClient':
            document.getElementById('addClientModal').classList.add('active');
            break;
        case 'calllog':
            document.getElementById('callLogModal').classList.add('active');
            renderCallLog(DEMO_DATA.callLog);
            break;
        case 'leadDetail':
            document.getElementById('leadDetailModal').classList.add('active');
            break;
    }
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
}

function openBabyChat(babyName) {
    const title = document.getElementById('babyChatTitle');
    title.textContent = `💬 Chat with ${babyName}`;

    const messages = document.getElementById('chatMessages');
    messages.innerHTML = `
        <div class="message ai">
            <div class="message-content">Hello! I'm ${babyName}, your AI assistant. How can I help you today?</div>
        </div>
    `;

    openModal('babyChat');
}

function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    const messages = document.getElementById('chatMessages');

    // Add user message
    messages.innerHTML += `
        <div class="message user">
            <div class="message-content">${message}</div>
        </div>
    `;

    // Simulate AI response
    setTimeout(() => {
        const responses = [
            "I can help you with that! Let me analyze the data...",
            "Based on the current metrics, I recommend focusing on callback timing.",
            "Carlos is performing exceptionally well. His techniques could be shared with the team.",
            "I've identified 3 high-priority leads that need immediate attention.",
            "The conversion rate can be improved by focusing on the morning call window."
        ];
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];

        messages.innerHTML += `
            <div class="message ai">
                <div class="message-content">${randomResponse}</div>
            </div>
        `;
        messages.scrollTop = messages.scrollHeight;
    }, 1000);

    input.value = '';
    messages.scrollTop = messages.scrollHeight;
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function openLeadDetail(leadId) {
    const lead = DEMO_DATA.leads.find(l => l.id === leadId);
    if (!lead) return;

    const body = document.getElementById('leadDetailBody');
    body.innerHTML = `
        <div class="form-group">
            <label>Status</label>
            <select>
                <option ${lead.status === 'red' ? 'selected' : ''}>🔴 Red (No/Rejected)</option>
                <option ${lead.status === 'orange' ? 'selected' : ''}>🟠 Orange (VM/Maybe)</option>
                <option ${lead.status === 'yellow' ? 'selected' : ''}>🟡 Yellow (Working)</option>
                <option ${lead.status === 'green' ? 'selected' : ''}>🟢 Green (Appointed)</option>
                <option ${lead.status === 'blue' ? 'selected' : ''}>🔵 Blue (Follow-up)</option>
            </select>
        </div>
        <div class="form-group">
            <label>Name</label>
            <input type="text" value="${lead.name}">
        </div>
        <div class="form-group">
            <label>Phone</label>
            <input type="text" value="${lead.phone}">
        </div>
        <div class="form-group">
            <label>Coordinator</label>
            <input type="text" value="${lead.coordinator}">
        </div>
        <div class="form-group">
            <label>Notes</label>
            <input type="text" value="${lead.notes}">
        </div>
        <div class="modal-actions">
            <button class="btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn-primary" onclick="saveLead(${lead.id})">Save Changes</button>
        </div>
    `;

    openModal('leadDetail');
}

function filterLeads() {
    const filter = document.getElementById('leadStatusFilter').value;
    let filteredLeads = DEMO_DATA.leads;

    if (filter !== 'all') {
        filteredLeads = DEMO_DATA.leads.filter(l => l.status === filter);
    }

    renderLeadsTable(filteredLeads);
}

// ═══════════════════════════════════════════════════════════════════
// FORM HANDLERS
// ═══════════════════════════════════════════════════════════════════

function handleAddClient(event) {
    event.preventDefault();
    alert('Client added successfully! (Demo mode)');
    closeModal();
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('columnMapping').style.display = 'block';
        document.getElementById('importPreview').style.display = 'block';

        // Demo mapping
        document.getElementById('mappingGrid').innerHTML = `
            <div class="form-group">
                <label>Name Column</label>
                <select><option>Column A</option><option>Column B</option></select>
            </div>
            <div class="form-group">
                <label>Phone Column</label>
                <select><option>Column B</option><option>Column C</option></select>
            </div>
        `;

        // Demo preview
        document.getElementById('previewTable').innerHTML = `
            <thead><tr><th>Name</th><th>Phone</th></tr></thead>
            <tbody>
                <tr><td>John Doe</td><td>(555) 111-2222</td></tr>
                <tr><td>Jane Smith</td><td>(555) 333-4444</td></tr>
                <tr><td>Bob Johnson</td><td>(555) 555-6666</td></tr>
            </tbody>
        `;
    }
}

function confirmImport() {
    alert('Leads imported successfully! (Demo mode)');
    closeModal();
}

function exportReport() {
    alert('Report exported! (Demo mode - would download Excel file)');
}

function saveLead(leadId) {
    alert('Lead saved successfully! (Demo mode)');
    closeModal();
}

function editLead(leadId) {
    openLeadDetail(leadId);
}
