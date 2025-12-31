# SCORPION - Smart Coordination Of Resources, Processes, Intelligence, Operations & Networks

> **Version 1.0.0 - TESTUDO Formation**
> Built December 29-31, 2024

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

SCORPION is a modular AI-powered business automation platform that orchestrates multiple AI "babies" (language models) to handle customer interactions, meeting transcription, quote generation, appointment scheduling, and CRM operations.

## Architecture Overview

```
                            ┌─────────────────────────────────────────┐
                            │              HEAD (Brain)               │
                            │  ┌─────────────┐   ┌─────────────────┐  │
                            │  │  ChromaDB   │   │     Ollama      │  │
                            │  │  (Memory)   │   │   (AI Babies)   │  │
                            │  └─────────────┘   └─────────────────┘  │
                            └───────────────────────┬─────────────────┘
                                                    │
              ┌─────────────────┬───────────────────┼───────────────────┬─────────────────┐
              │                 │                   │                   │                 │
     ┌────────▼────────┐ ┌──────▼──────┐   ┌───────▼───────┐   ┌───────▼───────┐ ┌───────▼───────┐
     │     CLAW 1      │ │   CLAW 2    │   │     MOUTH     │   │     BODY      │ │     TAIL      │
     │   Sales/CRM     │ │    LCMS     │   │    (API)      │   │   (Docker)    │ │  (Security)   │
     │ - Lead Capture  │ │ - Courses   │   │ - Dashboard   │   │ - Compose     │ │ - Access Ctrl │
     │ - Pipeline      │ │ - Students  │   │ - REST API    │   │ - Services    │ │ - Auth/Tokens │
     └─────────────────┘ └─────────────┘   └───────────────┘   └───────────────┘ └───────────────┘
                                                    │
              ┌─────────────────┬───────────────────┼───────────────────┬─────────────────┐
              │                 │                   │                   │                 │
     ┌────────▼────────┐ ┌──────▼──────┐   ┌───────▼───────┐   ┌───────▼───────┐ ┌───────▼───────┐
     │    LEG: OTTER   │ │ LEG: BRIDGE │   │   LEG: J3     │   │  LEG: NSIPA   │ │  LEG: Client  │
     │   Transcription │ │ Phone-Linux │   │ Construction  │   │  Healthcare   │ │   Template    │
     │ - Meetings      │ │ - Termux    │   │ - Quotes      │   │ - Call Logs   │ │ - Extensible  │
     │ - Summarize     │ │ - Sync      │   │ - Clients     │   │ - Appts       │ │ - Webhooks    │
     └─────────────────┘ └─────────────┘   └───────────────┘   └───────────────┘ └───────────────┘
```

## AI Babies

SCORPION uses specialized AI models (via Ollama) called "babies":

| Baby | Model | Role |
|------|-------|------|
| **MARCUS** | mistral | General intelligence, customer interaction |
| **HERMES** | phi | Fast responses, quick tasks |
| **ATHENA** | codellama | Code generation, technical analysis |
| **APOLLO** | llama2 | Creative writing, content generation |

## Features

### Core Modules

- **HEAD** - Central AI brain with ChromaDB memory and Ollama integration
- **CLAW1** - Sales lead capture and CRM pipeline management
- **CLAW2** - Learning Content Management System (LCMS)
- **MOUTH** - FastAPI REST dashboard and API gateway
- **BODY** - Docker infrastructure and service orchestration
- **TAIL** - Security, access control, and authentication

### LEG Modules (Client-Specific)

- **OTTER** - Meeting transcription and summarization with email notifications
- **BRIDGE** - Phone-Linux connection via Termux for mobile integration
- **J3** - Construction quote generation with PDF export
- **NSIPA** - Healthcare call logging and appointment tracking

### Integration & Tools

- **CLI** - Command-line interface for all SCORPION operations
- **JARVIS** - Automated task scheduler with 15+ predefined jobs
- **Health Monitor** - Service health checking and alerting
- **Backup System** - Automated backup with restore capability

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Ollama (for AI models)

### One-Command Install

```bash
curl -sSL https://raw.githubusercontent.com/yourrepo/scorpion/main/scripts/install.sh | bash
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourrepo/scorpion.git
cd scorpion

# Copy environment template
cp .env.example .env
# Edit .env with your settings

# Install Python dependencies
pip install -r body/docker/requirements.txt

# Pull AI models
ollama pull mistral
ollama pull phi
ollama pull codellama
ollama pull llama2

# Start with Docker
docker compose -f body/docker/docker-compose.yml up -d

# Or run directly
python -m integration.cli status
```

### Using the CLI

```bash
# Check system status
python -m integration.cli status

# Ask an AI baby a question
python -m integration.cli ask "What is the capital of France?"

# List available AI babies
python -m integration.cli babies

# Generate a quote (J3)
python -m integration.cli quote --client "John Doe" --project "Kitchen Remodel"

# Log a call (NSIPA)
python -m integration.cli log-call --caller "Jane Smith" --summary "Appointment inquiry"

# Capture a lead
python -m integration.cli lead --name "Bob Wilson" --email "bob@example.com"

# Search memories
python -m integration.cli search "construction project"

# View CRM pipeline
python -m integration.cli pipeline
```

## Project Structure

```
scorpion/
├── core/                   # Core configuration
│   ├── config.py          # Environment config loader
│   └── constants.py       # Global constants
├── head/                   # AI Brain (ChromaDB + Ollama)
├── claw1/                  # Sales & CRM
│   ├── sales/             # Lead capture
│   └── crm/               # Pipeline management
├── claw2/                  # Learning Management
│   └── lcms/              # Course management
├── mouth/                  # API Dashboard
│   └── api.py             # FastAPI application
├── body/                   # Infrastructure
│   └── docker/            # Docker configuration
├── tail/                   # Security
│   └── labienus/          # Access control
├── legs/                   # Client containers
│   └── template/          # LEG template
├── otter/                  # Meeting transcription
├── bridge/                 # Phone-Linux connection
├── j3/                     # Construction quotes
├── nsipa/                  # Healthcare call logging
├── integration/            # CLI & Scheduler
│   ├── cli.py             # Command-line interface
│   └── scheduler.py       # JARVIS scheduler
├── monitoring/             # Health monitoring
├── daemon/                 # Automation config
│   └── agenda.json        # Scheduled tasks
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── tests/                  # Test suite
├── .env.example           # Environment template
├── Makefile               # Development commands
└── README.md              # This file
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required settings
POSTGRES_PASSWORD=your-database-password
API_SECRET_KEY=your-secure-secret-key
OLLAMA_HOST=localhost
CHROMADB_HOST=localhost

# Optional: Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/test_imports.py -v
```

### Common Commands

```bash
make install      # Install dependencies
make test         # Run tests
make run          # Start development server
make docker-up    # Start Docker services
make docker-down  # Stop Docker services
make backup       # Create backup
make clean        # Clean cache files
```

### Adding a New LEG

1. Copy the template:
   ```bash
   cp -r legs/template legs/mynewleg
   ```

2. Customize `client_template.py` for your client

3. Register in `LegFactory`:
   ```python
   LegFactory.register_leg("industry", MyNewLeg)
   ```

## API Endpoints

The MOUTH API provides these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/ask` | Ask an AI baby |
| GET | `/babies` | List AI babies |
| GET | `/status` | System status |
| POST | `/leads` | Create lead |
| GET | `/pipeline` | View pipeline |
| POST | `/quotes` | Generate quote |
| POST | `/calls` | Log call |
| POST | `/search` | Search memories |

## Scheduled Tasks (JARVIS)

JARVIS runs these automated tasks:

| Task | Schedule | Description |
|------|----------|-------------|
| Health Check | Hourly | Monitor all services |
| Backup | Daily 2 AM | Full system backup |
| Stats Report | Daily 8 AM | Activity summary |
| Cleanup | Weekly | Remove old logs/temp |
| Optimization | Weekly | Database optimization |
| Lead Follow-up | Daily 9 AM | Check stale leads |
| Appointment Reminder | Daily 5 PM | Next-day reminders |

## Security

- Token-based authentication with PBKDF2 password hashing
- Access levels: HEAD (100), CLAW (75), LEG (50), PUBLIC (10)
- Webhook signature verification
- Environment-based secrets management

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints
- Write docstrings for public functions
- Add tests for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI powered by [Ollama](https://ollama.ai/)
- Vector search by [ChromaDB](https://www.trychroma.com/)
- Workflows by [n8n](https://n8n.io/)

---

**SCORPION v1.0.0 - TESTUDO Formation**

*"Like a Roman tortoise formation - impenetrable, coordinated, unstoppable."*
