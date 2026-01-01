# SCORPION Brain v1.0.0

> **New Year's Edition 2025** - AI-Powered Business Automation System

```
    ███████╗ ██████╗ ██████╗ ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
    ██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║██╔═══██╗████╗  ██║
    ███████╗██║     ██║   ██║██████╔╝██████╔╝██║██║   ██║██╔██╗ ██║
    ╚════██║██║     ██║   ██║██╔══██╗██╔═══╝ ██║██║   ██║██║╚██╗██║
    ███████║╚██████╗╚██████╔╝██║  ██║██║     ██║╚██████╔╝██║ ╚████║
    ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
```

## Overview

SCORPION Brain is a comprehensive AI automation system designed to streamline business operations across multiple client verticals. Built over 3 intensive days (Dec 29-31, 2024), this system integrates AI assistants ("babies"), client-specific modules ("legs"), and automated workflows.

## Quick Start

```bash
# Validate configuration
python start_scorpion.py --validate

# Start SCORPION
python start_scorpion.py

# Quick query to an AI baby
python scripts/quick_ask.py "What is Python?"

# Check system status
python scripts/check_babies.py

# Start dashboard
python scripts/dashboard_server.py
```

## System Architecture

### AI Babies (Assistants)

| Baby | Role | Specialty |
|------|------|-----------|
| **MARCUS** | General Assistant | Business strategy, lead analysis |
| **LUNA** | Data Analyst | Analytics, insights, reporting |
| **NOVA** | Creative Writer | Content creation, marketing |
| **ATLAS** | Research Expert | Deep research, knowledge gathering |
| **SAGE** | Code Expert | Development, technical solutions |

### Client Legs

Client-specific modules that handle industry-specific business logic:

| Leg | Client | Industry | Key Services |
|-----|--------|----------|--------------|
| **JoeLeg** | IPC Solutions | Call Center | Lead routing, call tracking, credit repair referrals |
| **JonathanLeg** | J3 Structural | Construction | Quote generation, estimate scheduling, project tracking |
| **AntonioLeg** | Banking Services | Banking | Lead scoring, compliance verification, consultations |
| **WillLeg** | Real Estate | Real Estate | Property matching, lead nurturing, open house management |

### n8n Workflows

Automated workflows for common operations:

| Workflow | Trigger | Description |
|----------|---------|-------------|
| **lead_intake.json** | Webhook | Process incoming leads through validation, scoring, and routing |
| **daily_digest.json** | 6pm Daily | Generate and email daily performance reports |
| **appointment_reminder.json** | Hourly | Send SMS reminders for upcoming appointments |

## Directory Structure

```
SCORPION_BRAIN/
├── start_scorpion.py          # Main entry point
├── README.md                  # This file
│
├── legs/                      # Client leg modules
│   ├── __init__.py
│   └── clients/
│       ├── __init__.py
│       ├── base_leg.py        # Base class for all legs
│       ├── joe_leg.py         # IPC Solutions
│       ├── jonathan_leg.py    # J3 Structural
│       ├── antonio_leg.py     # Banking Services
│       └── will_leg.py        # Real Estate
│
├── workflows/                 # n8n workflow templates
│   ├── __init__.py
│   ├── lead_intake.json
│   ├── daily_digest.json
│   └── appointment_reminder.json
│
├── scripts/                   # Utility scripts
│   ├── __init__.py
│   ├── quick_ask.py          # Query AI babies
│   ├── check_babies.py       # Check system status
│   └── dashboard_server.py   # Serve dashboard
│
├── dashboard/                 # Web dashboard
│   └── (dashboard files)
│
└── .github/
    └── pull_request_template.md
```

## API Reference

### Health Check
```
GET /api/health
```

### Query AI Baby
```
POST /api/babies/{baby_name}/query
Body: { "query": "Your question here" }
```

### Process Lead
```
POST /api/legs/{leg_name}/process
Body: { "lead": { ... lead data ... } }
```

### Get Daily Report
```
GET /api/legs/{leg_name}/daily_report
```

## Client Leg Usage

### Joe Leg (Call Center)
```python
from legs.clients import JoeLeg

joe = JoeLeg()
joe.initialize()

# Process a lead
result = joe.process_lead(lead)

# Log a call
call_id = joe.log_call(lead_id, agent_id, duration, disposition)

# Track conversion
joe.track_conversion(lead_id)

# Get daily report
report = joe.daily_report()
```

### Jonathan Leg (Construction)
```python
from legs.clients import JonathanLeg

jonathan = JonathanLeg()
jonathan.initialize()

# New project inquiry
project = jonathan.new_project_inquiry(client_data)

# Schedule estimate
estimate = jonathan.schedule_estimate(client_id, datetime)

# Update project status
jonathan.project_status_update(project_id, "in_progress")
```

### Antonio Leg (Banking)
```python
from legs.clients import AntonioLeg

antonio = AntonioLeg()
antonio.initialize()

# Score a financial lead
score = antonio.score_financial_lead(lead)

# Initiate compliance check
check = antonio.compliance_check(client_data)

# Schedule consultation
consultation = antonio.schedule_consultation(client_id)
```

### Will Leg (Real Estate)
```python
from legs.clients import WillLeg

will = WillLeg()
will.initialize()

# Match properties to buyer
matches = will.match_properties(buyer_criteria)

# Start nurture sequence
will.nurture_sequence(lead_id, "buyer_new")

# Send open house reminders
will.open_house_reminder(property_id, attendees)
```

## Build Stats

| Phase | Date | Components | Files | Lines |
|-------|------|------------|-------|-------|
| TESTUDO | Dec 29 | Otter, Bridge, J3, NSIPA | 27 | 7,296 |
| CLAWS + TAIL + MOUTH | Dec 30 | Data extraction, logging, comms | 13 | 2,862 |
| OVERNIGHT | Dec 30 | Body, integration, docs | 20 | 5,061 |
| FINAL | Dec 31 | Core, tests, configs | 12 | 2,496 |
| ENGINE | Dec 31 | Dashboard, babies, tools | 16 | 6,363 |
| CLIENT LEGS | Dec 31 | Joe, Jonathan, Antonio, Will | 12 | 1,500+ |
| **TOTAL** | **3 days** | **Complete System** | **100+** | **25,500+** |

## Configuration

### Environment Variables
```bash
SCORPION_HOME=/path/to/scorpion
SCORPION_API_PORT=8000
SCORPION_DASHBOARD_PORT=8888
ANTHROPIC_API_KEY=your-api-key
```

### Required Dependencies
```bash
pip install requests chromadb anthropic fastapi uvicorn
```

## Development

```bash
# Run in dev mode with hot reload
python start_scorpion.py --dev

# Run validation
python start_scorpion.py --validate

# Run tests (coming soon)
pytest tests/
```

## Support

For issues and feature requests, please open a GitHub issue.

---

**Built with Claude AI | New Year's Eve 2024 | Ready for 2025!**

*SCORPION is alive!*
