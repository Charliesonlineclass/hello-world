# SCORPION KING - System Architecture

```
███████╗ ██████╗ ██████╗ ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║██╔═══██╗████╗  ██║
███████╗██║     ██║   ██║██████╔╝██████╔╝██║██║   ██║██╔██╗ ██║
╚════██║██║     ██║   ██║██╔══██╗██╔═══╝ ██║██║   ██║██║╚██╗██║
███████║╚██████╗╚██████╔╝██║  ██║██║     ██║╚██████╔╝██║ ╚████║
╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                    AI AUTOMATION PLATFORM
```

## Overview

SCORPION (Systematic Cognitive Operations & Resource Processing for Intelligent Operational Networks) is a modular AI automation platform designed to handle business operations, client management, and intelligent task processing.

## Anatomical Overview

```
                            ┌─────────────────────────────────┐
                            │            🧠 HEAD              │
                            │    (AI Babies + Memory)         │
                            │  ┌─────────┐  ┌─────────┐      │
                            │  │ MARCUS  │  │ ATHENA  │      │
                            │  │ mistral │  │codellama│      │
                            │  └─────────┘  └─────────┘      │
                            │  ┌─────────┐  ┌─────────┐      │
                            │  │ HERMES  │  │ APOLLO  │      │
                            │  │   phi   │  │ llama2  │      │
                            │  └─────────┘  └─────────┘      │
                            │       ┌─────────────┐          │
                            │       │  ChromaDB   │          │
                            │       │  (Memory)   │          │
                            │       └─────────────┘          │
                            └───────────────┬─────────────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        │                                   │                                   │
        ▼                                   ▼                                   ▼
┌───────────────┐                   ┌───────────────┐                   ┌───────────────┐
│   🦀 CLAW 1   │                   │   🦀 CLAW 2   │                   │   👄 MOUTH    │
│   Sales/CRM   │                   │   Learning    │                   │   Dashboard   │
│               │                   │               │                   │               │
│ • Lead Capture│                   │ • Courses     │                   │ • REST API    │
│ • Pipeline    │                   │ • Enrollment  │                   │ • n8n Flows   │
│ • Scoring     │                   │ • Progress    │                   │ • WebSocket   │
└───────┬───────┘                   └───────┬───────┘                   └───────┬───────┘
        │                                   │                                   │
        └───────────────────────────────────┼───────────────────────────────────┘
                                            │
                            ┌───────────────┴───────────────┐
                            │          🏛️ BODY              │
                            │    (Docker Infrastructure)    │
                            │                               │
                            │  ┌─────────┐ ┌─────────┐     │
                            │  │ PostgreSQL│ │  Redis  │     │
                            │  └─────────┘ └─────────┘     │
                            │  ┌─────────┐ ┌─────────┐     │
                            │  │  Nginx  │ │ Metrics │     │
                            │  └─────────┘ └─────────┘     │
                            └───────────────┬───────────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        │                                   │                                   │
        ▼                                   ▼                                   ▼
┌───────────────┐                   ┌───────────────┐                   ┌───────────────┐
│   🦵 LEG: J3  │                   │  🦵 LEG: NSIPA │                   │ 🦵 LEG: OTHER │
│  Construction │                   │   Healthcare  │                   │   (Template)  │
│               │                   │               │                   │               │
│ • Quotes      │                   │ • Call Logs   │                   │ • Custom      │
│ • Clients     │                   │ • Appts       │                   │ • Isolated    │
│ • Automation  │                   │ • Reminders   │                   │ • Secure      │
└───────────────┘                   └───────────────┘                   └───────────────┘
                                            │
                            ┌───────────────┴───────────────┐
                            │          🦂 TAIL              │
                            │    (Security - LABIENUS)      │
                            │                               │
                            │  • Authentication             │
                            │  • Authorization              │
                            │  • Access Control             │
                            │  • Container Isolation        │
                            └───────────────────────────────┘
```

## Component Details

### HEAD (Brain Center)

The central intelligence layer powered by local AI models via Ollama.

| Baby | Model | Purpose | Best For |
|------|-------|---------|----------|
| MARCUS | mistral | Main Assistant | General tasks, balanced responses |
| HERMES | phi | Fast Responder | Quick queries, simple tasks |
| ATHENA | codellama | Code Expert | Programming, debugging, code review |
| APOLLO | llama2 | Creative | Writing, content, brainstorming |

**Memory Layer (ChromaDB)**
- Vector database for semantic search
- Stores embeddings of all conversations
- Meeting transcripts and summaries
- Knowledge base documents

### CLAW 1 (Sales & CRM)

Business development and customer relationship management.

```
claw1/
├── sales/
│   └── lead_capture.py     # Lead processing and scoring
│       ├── process_form()  # Validate incoming leads
│       ├── score_lead()    # Calculate priority 1-10
│       └── assign_to_leg() # Route to client container
│
└── crm/
    └── pipeline.py         # Sales pipeline management
        ├── Stages: new → contacted → quoted → negotiating → closed/lost
        ├── move_stage()    # Transition with rules
        └── get_stats()     # Pipeline analytics
```

### CLAW 2 (Learning Management)

Educational content and student tracking.

```
claw2/
└── lcms/
    └── course_manager.py
        ├── create_course()     # Build course structure
        ├── enroll_student()    # Student registration
        ├── track_progress()    # Completion tracking
        └── Certificate generation on completion
```

### MOUTH (API & Dashboard)

Unified interface for all SCORPION operations.

```
mouth/
└── api.py                  # FastAPI backend
    │
    ├── GET  /status        # System health
    ├── GET  /babies        # Available AI models
    ├── GET  /stats         # Aggregate statistics
    ├── GET  /pipeline      # Sales pipeline view
    │
    ├── POST /ask           # Query AI babies
    ├── POST /quote         # Generate J3 quote
    ├── POST /log-call      # Log NSIPA call
    └── POST /lead          # Submit new lead
```

### BODY (Infrastructure)

Docker-based infrastructure layer.

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: scorpion-net             │
│                       172.28.0.0/16                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  chromadb   │  │   ollama    │  │   n8n       │         │
│  │  :8000      │  │   :11434    │  │   :5678     │         │
│  │ 172.28.0.10 │  │ 172.28.0.11 │  │ 172.28.0.30 │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  postgres   │  │   redis     │  │   nginx     │         │
│  │  :5432      │  │   :6379     │  │   :80/:443  │         │
│  │ 172.28.0.40 │  │ 172.28.0.41 │  │ 172.28.0.2  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │              scorpion-brain                      │       │
│  │              :8080, :9876                        │       │
│  │              172.28.0.20                         │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### LEGS (Client Containers)

Isolated environments for each client/business.

| LEG | Purpose | Features |
|-----|---------|----------|
| J3 | Construction | Quote generation, client management |
| NSIPA | Healthcare | Call logging, appointment tracking |
| Template | New clients | Easily clonable for new businesses |

```
legs/
├── j3/                     # J3 Construction
│   ├── quotes/
│   ├── clients/
│   └── config.json
│
├── nsipa/                  # Healthcare
│   ├── call_logs/
│   ├── appointments/
│   └── config.json
│
└── template/               # New client template
    └── client_template.py
```

### TAIL (Security - LABIENUS)

Named after Titus Labienus, Caesar's trusted lieutenant.

```
Access Levels:
─────────────────────────────────────────────────────
  HEAD (100)   │ Full system access - Commander only
  CLAW (75)    │ Business unit access - Managers
  LEG  (50)    │ Container-specific - Workers
  PUBLIC (10)  │ Read-only public content
─────────────────────────────────────────────────────

Security Features:
  • Token-based authentication
  • Role-based access control (RBAC)
  • Container isolation for LEG users
  • API key validation
  • Failed login lockout
  • Audit logging
```

## Port Allocations

| Port | Service | Description |
|------|---------|-------------|
| 80 | Nginx | HTTP entry point |
| 443 | Nginx | HTTPS entry point |
| 5432 | PostgreSQL | Database |
| 5678 | n8n | Workflow automation |
| 6379 | Redis | Cache |
| 8000 | ChromaDB | Vector database |
| 8080 | MOUTH API | Dashboard backend |
| 9876 | BRIDGE | Phone access API |
| 11434 | Ollama | AI models |

## Data Flow

### Lead Processing Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Website │────▶│  MOUTH   │────▶│  CLAW1   │────▶│   LEG    │
│   Form   │     │   API    │     │  Scoring │     │ Container│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │                │
                      ▼                ▼
                 ┌──────────┐    ┌──────────┐
                 │ ChromaDB │    │ Pipeline │
                 │  Store   │    │  Stage   │
                 └──────────┘    └──────────┘
```

### AI Query Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   User   │────▶│  MOUTH   │────▶│  Ollama  │────▶│  Baby    │
│  Query   │     │   API    │     │  Proxy   │     │ (model)  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │                                  │
                      ▼                                  ▼
                 ┌──────────┐                      ┌──────────┐
                 │ ChromaDB │◀─────────────────────│ Response │
                 │ Context  │                      │          │
                 └──────────┘                      └──────────┘
```

## Integration Points

### OTTER (Meeting Transcription)

```
Audio File → Whisper → Transcript → LLM Summary → ChromaDB
     │                      │              │
     └──────────────────────┴──────────────┴──▶ Email Notification
```

### BRIDGE (Phone Access)

```
┌─────────────────┐          ┌─────────────────┐
│  Android Phone  │◀────────▶│  Linux Server   │
│    (Termux)     │   HTTP   │    (BRIDGE)     │
│                 │  :9876   │                 │
│  termux_client  │          │  phone_server   │
└─────────────────┘          └─────────────────┘
```

## File Structure

```
SCORPION_BRAIN/
├── body/
│   └── docker/
│       ├── docker-compose.yml
│       ├── Dockerfile.brain
│       └── nginx/, postgres/, redis/
│
├── bridge/                 # Phone → Linux
│   ├── phone_server.py
│   └── termux_client.py
│
├── claw1/                  # Sales & CRM
│   ├── sales/
│   └── crm/
│
├── claw2/                  # Learning
│   └── lcms/
│
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   └── QUICKSTART.md
│
├── integration/            # CLI & Scheduler
│   ├── cli.py
│   └── scheduler.py
│
├── j3/                     # Construction LEG
├── nsipa/                  # Healthcare LEG
├── legs/template/          # LEG template
│
├── monitoring/             # Health checks
├── mouth/                  # Dashboard API
├── otter/                  # Transcription
├── scripts/                # Install/backup
└── tail/                   # Security
```

## Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                        EXTERNAL                              │
│  (Internet / Untrusted)                                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │      Nginx        │  ← SSL Termination
                    │   (Rate Limit)    │  ← WAF Rules
                    └─────────┬─────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ┌────▼────┐         ┌─────▼─────┐        ┌────▼────┐
    │  MOUTH  │         │    n8n    │        │ BRIDGE  │
    │  (API)  │         │(Workflows)│        │ (Phone) │
    └────┬────┘         └─────┬─────┘        └────┬────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │     LABIENUS      │  ← Auth/AuthZ
                    │   (Tail/Security) │  ← Token Validation
                    └─────────┬─────────┘
                              │
┌─────────────────────────────┼───────────────────────────────┐
│                        INTERNAL                              │
│  (Trusted Network - scorpion-net)                           │
│                                                             │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│    │ ChromaDB │  │  Ollama  │  │ Postgres │  │  Redis   │  │
│    └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Modes

| Mode | Command | Use Case |
|------|---------|----------|
| Development | `docker-compose up` | Local testing |
| Production | `docker-compose --profile prod up -d` | Live deployment |
| Minimal | `docker-compose up chromadb scorpion-brain` | Resource constrained |

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────┐
│                    Health Monitoring                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Service Checks:                                            │
│    • ChromaDB heartbeat                                     │
│    • Ollama model availability                              │
│    • API endpoint responses                                 │
│    • Database connections                                   │
│    • Redis ping                                             │
│                                                             │
│  Metrics:                                                   │
│    • Request latency                                        │
│    • Model inference time                                   │
│    • Queue depths                                           │
│    • Error rates                                            │
│                                                             │
│  Logs:                                                      │
│    • Centralized logging to /logs                           │
│    • Structured JSON format                                 │
│    • Log rotation (30 days)                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*SCORPION KING - Where AI Meets Automation* 🦂
