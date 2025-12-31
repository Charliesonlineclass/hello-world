# SCORPION KING - Quick Start Guide

Get SCORPION running in 5 minutes!

```
███████╗ ██████╗ ██████╗ ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║██╔═══██╗████╗  ██║
███████╗██║     ██║   ██║██████╔╝██████╔╝██║██║   ██║██╔██╗ ██║
╚════██║██║     ██║   ██║██╔══██╗██╔═══╝ ██║██║   ██║██║╚██╗██║
███████║╚██████╗╚██████╔╝██║  ██║██║     ██║╚██████╔╝██║ ╚████║
╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                         QUICK START
```

## Prerequisites

Before starting, ensure you have:

- [ ] **Docker** (20.10+) and **Docker Compose** (2.0+)
- [ ] **Git** for cloning the repository
- [ ] **Python 3.11+** (for local development)
- [ ] **8GB+ RAM** (recommended for AI models)
- [ ] **50GB+ disk space** (for models and data)

### Check Prerequisites

```bash
# Check Docker
docker --version          # Should be 20.10+
docker-compose --version  # Should be 2.0+

# Check Python
python3 --version         # Should be 3.11+

# Check Git
git --version
```

## Step 1: Clone Repository

```bash
# Clone SCORPION
git clone https://github.com/Charliesonlineclass/hello-world.git SCORPION_BRAIN
cd SCORPION_BRAIN
```

## Step 2: Install Ollama (AI Backend)

SCORPION uses Ollama for local AI models.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Pull required models (this may take a while)
ollama pull mistral      # MARCUS - Main assistant
ollama pull phi          # HERMES - Fast responder
ollama pull codellama    # ATHENA - Code expert
ollama pull llama2       # APOLLO - Creative writer

# Verify models
ollama list
```

## Step 3: Run Installation Script

```bash
# Make script executable
chmod +x scripts/install.sh

# Run installer
./scripts/install.sh
```

Or manually:

```bash
# Create directories
mkdir -p data logs transcripts quotes

# Copy environment template
cp body/docker/.env.example body/docker/.env

# Edit configuration (optional)
nano body/docker/.env

# Start services
cd body/docker
docker-compose up -d
```

## Step 4: Verify Installation

```bash
# Check all containers are running
docker-compose ps

# Expected output:
# NAME                  STATUS
# scorpion-brain       Up (healthy)
# scorpion-chromadb    Up (healthy)
# scorpion-nginx       Up
# scorpion-n8n         Up
# scorpion-postgres    Up (healthy)
# scorpion-redis       Up (healthy)
```

### Check Services

```bash
# ChromaDB
curl http://localhost:8000/api/v1/heartbeat
# Expected: {"nanosecond heartbeat":...}

# SCORPION API
curl http://localhost:8080/health
# Expected: {"status":"healthy"}

# Ollama
curl http://localhost:11434/api/tags
# Expected: {"models":[...]}
```

## Step 5: First API Call

### Using cURL

```bash
# Ask MARCUS a question
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: scorpion-key" \
  -d '{"baby": "marcus", "prompt": "What can you help me with?"}'
```

### Using the CLI

```bash
# Install CLI dependencies
pip install rich click colorama requests

# Ask a question
python -m integration.cli ask marcus "Hello, what can you do?"

# Check system status
python -m integration.cli status
```

## Step 6: Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| SCORPION API | http://localhost:8080/docs | API Key: `scorpion-key` |
| n8n Workflows | http://localhost:5678 | User: `commander` / Pass: `scorpion` |
| ChromaDB | http://localhost:8000 | Token: `scorpion-chroma-key` |

## Quick Test Commands

### Test AI Babies

```bash
# MARCUS - General assistant
python -m integration.cli ask marcus "Summarize what SCORPION is"

# HERMES - Quick answers
python -m integration.cli ask hermes "What is 2+2?"

# ATHENA - Code help
python -m integration.cli ask athena "Write a Python hello world"

# APOLLO - Creative
python -m integration.cli ask apollo "Write a haiku about automation"
```

### Test Business Modules

```bash
# Generate a quote
python -m integration.cli quote framing 1500 --materials premium

# Log a call
python -m integration.cli log-call "John Smith" 555-1234 scheduled

# Submit a lead
python -m integration.cli lead "Jane Doe" jane@email.com --company "Acme Inc"
```

## Common Issues

### "Cannot connect to Docker daemon"

```bash
# Start Docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### "Ollama models not found"

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve &

# Pull models again
ollama pull mistral
```

### "Port already in use"

```bash
# Check what's using the port
sudo lsof -i :8080

# Stop the process or change the port in .env
```

### "Out of memory"

```bash
# Use smaller models
ollama pull phi  # Instead of mistral

# Or increase Docker memory limit
# Edit Docker Desktop settings → Resources → Memory
```

## Environment Variables

Create/edit `body/docker/.env`:

```bash
# API Keys
SCORPION_API_KEY=your-secure-key
CHROMA_AUTH_TOKEN=your-chroma-key

# Database
POSTGRES_USER=scorpion
POSTGRES_PASSWORD=secure-password

# n8n
N8N_USER=commander
N8N_PASSWORD=secure-password

# Ollama
OLLAMA_HOST=http://host.docker.internal:11434
```

## Directory Structure

After installation:

```
SCORPION_BRAIN/
├── body/docker/         # Docker configuration
├── data/                # Persistent data
├── logs/                # Log files
├── transcripts/         # Meeting transcripts
├── quotes/              # Generated quotes
├── otter/               # Transcription module
├── bridge/              # Phone access
├── j3/                  # Construction module
├── nsipa/               # Healthcare module
├── claw1/               # Sales/CRM
├── claw2/               # Learning
├── mouth/               # API
├── tail/                # Security
├── integration/         # CLI & Scheduler
└── monitoring/          # Health checks
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8080/docs
2. **Create Workflows**: Access n8n at http://localhost:5678
3. **Configure Security**: Update API keys in `.env`
4. **Add Knowledge**: Upload documents to ChromaDB
5. **Set Up Phone Access**: See `bridge/TERMUX_SETUP.md`

## Useful Commands

```bash
# View logs
docker-compose logs -f scorpion-brain

# Restart a service
docker-compose restart scorpion-brain

# Stop all services
docker-compose down

# Stop and remove data
docker-compose down -v

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Enter container shell
docker exec -it scorpion-brain /bin/bash

# Run health check
python -m monitoring.health_check

# Backup data
./scripts/backup.sh
```

## Getting Help

- **Documentation**: See `docs/ARCHITECTURE.md`
- **Issues**: https://github.com/Charliesonlineclass/hello-world/issues
- **CLI Help**: `python -m integration.cli --help`

---

*You're now ready to use SCORPION!* 🦂

```
 _____ _   _  _____ _____ _____ _____ _____
/  ___| | | |/  __ \_   _|  ___/  ___/  ___|
\ `--.| | | || /  \/ | | | |__ \ `--.\ `--.
 `--. \ | | || |     | | |  __| `--. \`--. \
/\__/ / |_| || \__/\ | | | |___/\__/ /\__/ /
\____/ \___/  \____/ \_/ \____/\____/\____/
```
