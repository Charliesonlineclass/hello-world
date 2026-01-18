# SCORPION CRM

> Lead management system for J3 Construction and beyond.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the API server
cd mouth && uvicorn crm_api:app --port 9999 --reload

# 3. Open dashboards in browser
# Admin: castle/admin_dashboard.html
# Agent: castle/agent_dashboard.html
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      SCORPION CRM                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│   │   Admin     │     │   Agent     │     │   Lead      │  │
│   │  Dashboard  │     │  Dashboard  │     │   Form      │  │
│   │  (Desktop)  │     │  (Mobile)   │     │  (Mobile)   │  │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘  │
│          │                   │                   │          │
│          └───────────────────┼───────────────────┘          │
│                              │                              │
│                              ▼                              │
│                    ┌─────────────────┐                      │
│                    │   FastAPI CRM   │                      │
│                    │   (port 9999)   │                      │
│                    └────────┬────────┘                      │
│                             │                               │
│                             ▼                               │
│                    ┌─────────────────┐                      │
│                    │  SQLite (crm.db)│                      │
│                    └─────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
hello-world/
├── mouth/
│   └── crm_api.py           # FastAPI backend (port 9999)
├── castle/
│   ├── admin_dashboard.html # Admin panel (stats, leads, agents)
│   └── agent_dashboard.html # Agent mobile app
├── legs/j3/lead_tracker/
│   └── lead_form.html       # Lead entry form
├── data/
│   └── schema.sql           # SQLite database schema
├── requirements.txt         # Python dependencies
├── CLAUDE.md               # AI agent rules
├── CAN_OF_WORMS.md         # Task tracker
└── README.md               # This file
```

---

## API Endpoints

Base URL: `http://localhost:9999`

### Leads
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/leads` | Create lead (auto-calculates score) |
| GET | `/leads` | List leads (filter: `?agent=X&status=Y`) |
| GET | `/leads/{id}` | Get single lead |
| PUT | `/leads/{id}` | Update lead |
| DELETE | `/leads/{id}` | Delete lead |

### Pipeline & Stats
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pipeline` | Leads grouped by status |
| GET | `/stats` | Conversion rates, agent performance |

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents` | Create agent |
| GET | `/agents` | List all agents |

---

## Lead Scoring

Leads are automatically scored (0-75 points):

| Factor | Value | Points |
|--------|-------|--------|
| **Urgency** | ASAP | 30 |
| | Soon | 15 |
| | Later | 5 |
| **Budget** | $30k+ | 25 |
| | $15-30k | 20 |
| | $5-15k | 10 |
| | Under $5k | 5 |
| **Project** | Full Renovation | 20 |
| | Kitchen | 15 |
| | Bathroom | 12 |
| | Other | 8 |

**Score Tiers:**
- 60+ = Fire (Hot lead, act immediately)
- 50-59 = Hot (High priority)
- 40-49 = Warm (Follow up soon)
- <40 = Cold (Nurture over time)

---

## Dashboards

### Admin Dashboard (`castle/admin_dashboard.html`)
- Stats overview: total leads, hot leads, conversion rate, pipeline value
- Agent performance table
- Full leads table with filters
- Bulk assign/delete actions
- Import CSV / Export Excel

### Agent Dashboard (`castle/agent_dashboard.html`)
- Mobile-first design
- Simple name login
- Shows only assigned leads
- Update status, call/text buttons
- Auto-refresh every 30 seconds

---

## Development

### Database Reset
```bash
rm data/crm.db
sqlite3 data/crm.db < data/schema.sql
```

### Add Sample Data
Uncomment the INSERT statements in `data/schema.sql` and run:
```bash
sqlite3 data/crm.db < data/schema.sql
```

### Testing the API
```bash
# Create a lead
curl -X POST http://localhost:9999/leads \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","contact":"555-1234","project_type":"kitchen","urgency":"asap","budget":"15to30k"}'

# Get all leads
curl http://localhost:9999/leads

# Get stats
curl http://localhost:9999/stats
```

---

## Deployment

### Local Network
```bash
uvicorn crm_api:app --host 0.0.0.0 --port 9999
```

### Cloudflare Tunnel
```bash
cloudflared tunnel run scorpion
```

### Production Checklist
- [ ] Set up HTTPS via Cloudflare
- [ ] Add proper authentication
- [ ] Configure CORS for production domain
- [ ] Set up database backups
- [ ] Add rate limiting

---

## Roadmap

See `CAN_OF_WORMS.md` for the full task list.

**Next Up:**
- Cloudflare tunnel with SSL
- Phone bridge for OCR lead capture
- Email automation for Excel reports
- Whisper voice-to-lead integration

---

## License

Private - SCORPION Empire

---

*Built with FastAPI, SQLite, and vanilla JavaScript.* 🦂
