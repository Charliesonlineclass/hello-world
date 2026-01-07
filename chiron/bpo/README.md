# ⚔️ CHIRON BPO COMMAND

Military-grade Business Process Outsourcing management system.

## Overview

CHIRON (named after the wise centaur who trained heroes) is a complete BPO operations platform designed for healthcare call centers. Built with military precision and efficiency.

## Features

- **Real-time Agent Tracking** - Live status, calls, appointments, quality scores
- **Queue Monitoring** - Visual queue with wait times and SLA alerts
- **Disposition Management** - Full healthcare disposition code library
- **Script System** - Complete call scripts with objection rebuttals
- **Performance Analytics** - Hourly, daily, and weekly metrics
- **Leaderboard** - Real-time performance ranking

## Quick Start

```bash
# Navigate to BPO directory
cd chiron/bpo

# Start the API server
python -m uvicorn bpo_api:router --host 0.0.0.0 --port 8801

# Open dashboard
firefox http://localhost:8801/api/bpo/dashboard
```

## Architecture

```
chiron/bpo/
├── bpo_core.py      # Core engine classes (Agent, Call, Campaign)
├── bpo_api.py       # FastAPI REST endpoints
├── dashboard.html   # Real-time military-style dashboard
├── dispositions.py  # Healthcare call outcome codes
├── scripts.py       # Call scripts and rebuttals
└── README.md        # This file
```

## API Endpoints

### Agent Management
```
POST /api/bpo/clock-in          # Agent starts shift
POST /api/bpo/clock-out         # Agent ends shift
POST /api/bpo/status            # Update agent status
GET  /api/bpo/agents            # List all agents
GET  /api/bpo/agents/{id}       # Get agent details
```

### Call Tracking
```
POST /api/bpo/call/start        # Start call tracking
POST /api/bpo/call/end          # End call with disposition
POST /api/bpo/disposition       # Log disposition
```

### Queue Management
```
GET  /api/bpo/queue             # Queue status
POST /api/bpo/queue/add         # Add lead to queue
POST /api/bpo/queue/next        # Get next from queue
```

### Analytics
```
GET  /api/bpo/leaderboard       # Performance ranking
GET  /api/bpo/stats/realtime    # Dashboard stats
GET  /api/bpo/stats/hourly      # Hourly breakdown
```

## Disposition Codes

### Positive (Green)
- `APT_SET` - Appointment Set (+10 points)
- `TRANSFER` - Transferred to Closer (+5 points)
- `CALLBACK_HOT` - Hot Callback (+4 points)

### Neutral (Yellow/Blue)
- `CALLBACK` - Callback Scheduled (+3 points)
- `VOICEMAIL` - Left Voicemail (+1 point)
- `NO_ANSWER` - No Answer (0 points)

### Negative (Red)
- `NOT_INTERESTED` - Declined (0 points)
- `DO_NOT_CALL` - DNC Request (-1 point)
- `WRONG_NUMBER` - Bad Number (0 points)

## Scripts

The NSIPA wellness script includes:

1. **Opener** - Professional introduction
2. **Verify** - Confirm patient identity
3. **Pitch** - Benefits explanation
4. **Qualify** - Eligibility questions
5. **Close** - Appointment scheduling
6. **Confirm** - Details verification

### Built-in Rebuttals
- "Not interested" → Emphasize FREE benefit
- "Already have doctor" → This enhances existing care
- "Call me back" → Schedule specific callback
- "Too busy" → Quick 30-second booking
- "Send information" → Soft close while collecting email

## Color Scheme

```
Background:   #0a0a0f (Military Dark)
Primary:      #00ff41 (Terminal Green)
Secondary:    #00d4ff (Cyan)
Warning:      #ffcc00 (Yellow)
Danger:       #ff3333 (Red)
```

## Performance Metrics

- **Conversion Rate**: Appointments / Calls × 100
- **AHT (Average Handle Time)**: Talk + Hold + Wrap / Calls
- **Quality Score**: Based on call monitoring (0-100)
- **Points**: Accumulated from dispositions

## Integration

CHIRON BPO integrates with SCORPION EMPIRE:

```python
# In empire/api/main.py
from chiron.bpo.bpo_api import router as bpo_router
app.include_router(bpo_router)
```

---

**⚔️ CHIRON BPO COMMAND** - Military-grade precision for call center excellence

*Part of the 🦂 SCORPION AI ecosystem*
