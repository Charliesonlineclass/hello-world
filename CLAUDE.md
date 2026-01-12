# CLAUDE.md - SCORPION AI Agent Rules

## Project: SCORPION_BRAIN
**Owner:** Commander CE
**Purpose:** Unified business automation platform

---

## Architecture Overview

```
SCORPION_BRAIN/
├── factory/          # Tool generation system
│   ├── tool_factory.py
│   ├── blueprints/   # Tool templates
│   └── forge/        # Generated tools
├── mouth/            # API backends
│   └── crm_api.py    # FastAPI CRM (port 9999)
├── castle/           # Dashboards
│   ├── agent_dashboard.html
│   └── admin_dashboard.html
├── legs/             # Project-specific code
│   ├── j3/           # J3 Construction
│   ├── nsipa/        # NSIPA leads
│   └── bazaar/       # Marketplace
├── bridge/           # Phone integration
│   └── phone_bridge.py
├── data/             # Databases
│   └── crm.db
└── CAN_OF_WORMS.md   # Task tracker
```

---

## Core Rules for AI Agents

### 1. Code Standards
- Python 3.10+ syntax
- Type hints for all functions
- Docstrings for public methods
- Error handling with try/except
- No hardcoded secrets (use .env)

### 2. File Naming
- Python: snake_case.py
- HTML: kebab-case.html or snake_case.html
- Configs: UPPERCASE.md or lowercase.json

### 3. API Standards
- All APIs use FastAPI
- CORS enabled for development
- JSON responses only
- Pydantic models for validation
- SQLite for local storage

### 4. Frontend Standards
- Mobile-first responsive design
- Dark theme (bg: #1a1a2e, accent: #f59e0b)
- Vanilla JS (no frameworks)
- fetch() for API calls
- Error handling with user feedback

### 5. Git Workflow
- Commit after each task
- Descriptive commit messages
- Never commit secrets or .env files
- Branch naming: feature/name or fix/name

---

## Quick Commands

```bash
# Start CRM API
cd mouth && uvicorn crm_api:app --port 9999 --reload

# Initialize database
sqlite3 data/crm.db < data/schema.sql

# Serve dashboards (simple)
python -m http.server 8000 --directory castle

# Expose via Cloudflare
cloudflared tunnel run scorpion
```

---

## Project-Specific Context

### J3 Construction (legs/j3/)
- Lead management for contractors
- Client: Gio
- Domain: j3.ometech.org
- Focus: Kitchen/bathroom renovations

### NSIPA (legs/nsipa/)
- Government lead system
- Timesheet automation
- PDF form processing

### Bazaar (legs/bazaar/)
- Marketplace platform
- Hispanic worker matching
- Payment processing

---

## AI Agent Instructions

When working on this codebase:

1. **Read First**: Always read existing files before modifying
2. **Complete Code**: Write full implementations, no placeholders
3. **Test Locally**: Ensure code runs without syntax errors
4. **Commit Often**: Git commit after each completed task
5. **Update Tracker**: Mark tasks in CAN_OF_WORMS.md as done
6. **Mobile First**: Test at 375px width for mobile
7. **Dark Theme**: Use the established color scheme
8. **API Consistency**: Follow existing endpoint patterns

---

## Secrets & Environment

Never commit these files:
- .env
- *.pem
- credentials.json
- cloudflared config with tokens

Store secrets in:
- Environment variables
- .env file (gitignored)
- Cloudflare dashboard (for tunnels)

---

*"The scorpion strikes with precision. Every line of code serves a purpose."* 🦂
