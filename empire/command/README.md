# SCORPION Command Center

Hierarchical drill-down dashboard for managing the SCORPION EMPIRE.

## Overview

The Command Center provides 3 zoom levels for navigating your business:

| Level | View | What You See |
|-------|------|--------------|
| **1** | 8 Eyes | All 8 client cards, minimal stats |
| **2** | Client Zoom | All accounts/projects for ONE client |
| **3** | Full Panel | Complete metrics dashboard |

**Click to zoom in, breadcrumb to zoom out.**

## File Structure

```
empire/command/
├── command_center.html    # Main SPA (single-page app)
├── css/
│   └── command.css        # All styles and animations
├── js/
│   ├── command.js         # State management & navigation
│   └── demo_data.js       # Offline demo data
├── components/
│   ├── babies_panel.html  # 12 Babies sidebar
│   └── modals.html        # All modal components
└── README.md              # This file
```

## Features

### View 1: 8 Eyes (Empire Overview)
- 2x4 grid of client cards
- Quick stats: Calls, Appointments, Conversion, MRR
- Color coding: Active (cyan), Paused (red), Empty (dashed)
- Bottom stats bar with totals

### View 2: Client Zoom
- Client header with full stats
- Accounts/Projects/Jobs grid
- Different card types per client industry

### View 3: Full Metrics
- **Coordinator Scorecard** - Ranked list with progress bars
- **Lead Tracker** - Status bars (Red/Orange/Yellow/Green/Blue)
- **Weekly Chart** - Calls vs Appointments (Chart.js)
- **Quick Actions** - Import, Export, Chat, Call Log

### 12 Babies Sidebar
- All 12 AI assistants listed
- Online/Offline status
- Click to open chat modal

### Modals
1. **Baby Chat** - Chat with any AI assistant
2. **Lead Detail** - Full lead info + edit
3. **Import Excel** - File upload + column mapping
4. **Add Client** - New client form
5. **Call Log** - Recent calls table
6. **All Leads** - Filterable leads table

## Demo Mode

Works completely offline with hardcoded demo data including:
- 5 active clients + 3 empty slots
- Joe/IPC with 7 accounts and full coordinator data
- Carlos Barahona as top performer (#1)
- Sample leads, call logs, and weekly stats

## Usage

Simply open `command_center.html` in any modern browser.

```bash
# From terminal
open empire/command/command_center.html

# Or use Python server
python -m http.server 8000
# Then visit http://localhost:8000/empire/command/command_center.html
```

## Color Scheme

- **Background**: #0a0a0f (dark)
- **Cards**: #12121a
- **Gold**: #ffd700 (primary accent)
- **Cyan**: #00d4ff (secondary accent)
- **Green**: #00d97e (success)
- **Red**: #e74c3c (danger/paused)
- **Orange**: #f39c12 (warning)

## Responsive Design

- Desktop: 4 cards per row
- Tablet: 2 cards per row
- Mobile: 1 card per row, stacked views

## API Integration (Future)

When backend is ready, the following endpoints will be used:

```
GET /api/empire/clients           - All clients for 8 eyes
GET /api/empire/clients/{id}/accounts - Client's accounts
GET /api/health/leads?account_id={id} - Healthcare leads
GET /api/health/stats?account_id={id} - Stats for scorecard
GET /api/projects/tasks?client_id={id} - J3 style tasks
GET /api/workforce/jobs?client_id={id} - Cruz style jobs
```

---

**SCORPION AI** - Because your best performer shouldn't be your only performer
