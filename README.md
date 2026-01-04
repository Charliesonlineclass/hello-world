# 🦂 SCORPION AI - Pandora's Castle

> AI-Powered Business Automation with Rent-to-Own Model

A complete business website with integrated CRM, AI chat assistants, and client portal. Built for **Ometeolt** - transforming businesses through accessible AI technology.

```
╔═══════════════════════════════════════════════════════════════╗
║              🏰 PANDORA'S CASTLE - SYSTEM OVERVIEW            ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  LAYER 1: CMS (Public Website)                               ║
║  ├── Homepage, Services, Pricing, Portfolio, Contact         ║
║  └── AI Chat Widget (HERMES)                                 ║
║                                                               ║
║  LAYER 2: CRM (Admin Dashboard)                              ║
║  ├── Lead Pipeline Management                                ║
║  ├── Client Profiles & Ownership Tracking                    ║
║  └── Project & Communication Management                      ║
║                                                               ║
║  LAYER 3: Client Portal                                      ║
║  ├── Dedicated AI Chat (VULCAN/MARCUS)                       ║
║  ├── Project Status & Timeline                               ║
║  └── Support Tickets                                         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai/) (optional, for AI features)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/pandoras-castle.git
cd pandoras-castle

# Install dependencies
pip install -r requirements.txt

# Initialize database with demo data
python scripts/seed_demo.py

# Start the castle!
python scripts/start_castle.py
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Website | http://localhost:8080 | Public-facing website |
| API | http://localhost:9999 | REST API endpoints |
| API Docs | http://localhost:9999/docs | Swagger documentation |
| Admin | http://localhost:8080/dashboard/ | Admin dashboard |
| Portal | http://localhost:8080/portal/login.html | Client portal |

### Demo Credentials

**Client Portal:**
- Email: `j3@structural.com`
- Password: `demo123`

## 📁 Project Structure

```
pandoras-castle/
├── website/                 # Public website
│   ├── index.html          # Homepage
│   ├── services.html       # Services page
│   ├── pricing.html        # Pricing page
│   ├── portfolio.html      # Portfolio/case studies
│   ├── contact.html        # Contact form
│   ├── css/style.css       # Custom styles
│   └── js/
│       ├── main.js         # Main JavaScript
│       └── chat-widget.js  # AI chat widget
│
├── crm/                     # CRM Backend
│   ├── models.py           # Data models
│   ├── database.py         # SQLite operations
│   ├── leads.py            # Lead management
│   ├── clients.py          # Client management
│   ├── projects.py         # Project management
│   └── communications.py   # Communication logging
│
├── api/                     # FastAPI Backend
│   ├── main.py             # Application entry
│   └── routes/
│       ├── leads.py        # Lead endpoints
│       ├── clients.py      # Client endpoints
│       ├── chat.py         # AI chat endpoints
│       └── admin.py        # Admin endpoints
│
├── dashboard/               # Admin Dashboard
│   ├── index.html          # Dashboard overview
│   ├── leads.html          # Lead management
│   ├── clients.html        # Client management
│   └── js/admin.js         # Dashboard JavaScript
│
├── portal/                  # Client Portal
│   ├── login.html          # Client login
│   ├── dashboard.html      # Client dashboard
│   ├── chat.html           # AI chat interface
│   ├── projects.html       # Project status
│   └── support.html        # Support tickets
│
├── config/                  # Configuration
│   ├── settings.py         # Application settings
│   └── babies.py           # AI assistant configs
│
├── scripts/                 # Utility Scripts
│   ├── start_castle.py     # Start all services
│   └── seed_demo.py        # Seed demo data
│
├── docker/                  # Docker Configuration
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── requirements.txt         # Python dependencies
```

## 🤖 AI Assistants (Babies)

| Name | Model | Tier | Purpose |
|------|-------|------|---------|
| HERMES | tinyllama | Starter | Fast public chat, lead capture |
| VULCAN | phi3:mini | Pro | Technical problem solving |
| MARCUS | qwen2.5:7b | Empire | Strategic analysis |

### Setting Up Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull required models
ollama pull tinyllama
ollama pull phi3:mini
ollama pull qwen2.5:7b
```

## 💰 Rent-to-Own Model

The unique business model allows clients to:
1. **Start Using** - AI is live from day one
2. **Build Equity** - Each payment builds ownership
3. **Own Forever** - After 12 months, no more payments

| Tier | Monthly | Total to Own | AI Baby |
|------|---------|--------------|---------|
| Starter | $100 | $1,200 | HERMES |
| Pro | $200 | $2,400 | VULCAN |
| Empire | $500 | $6,000 | MARCUS |

## 🐳 Docker Deployment

```bash
cd docker

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f castle

# Stop services
docker-compose down
```

## 📡 API Endpoints

### Leads
- `POST /api/leads/website` - Capture website lead
- `POST /api/leads/chat` - Capture chat lead
- `GET /api/leads` - List leads
- `GET /api/leads/pipeline` - Pipeline stats
- `PUT /api/leads/{id}/status` - Update status
- `POST /api/leads/{id}/convert` - Convert to client

### Clients
- `GET /api/clients` - List clients
- `GET /api/clients/{id}` - Get client
- `GET /api/clients/{id}/ownership` - Ownership status
- `POST /api/clients/{id}/payment` - Record payment

### Chat
- `POST /api/chat/public` - Public chat (rate limited)
- `POST /api/chat/client` - Authenticated client chat

### Admin
- `GET /api/admin/dashboard` - Dashboard stats
- `GET /api/admin/revenue` - Revenue metrics
- `POST /api/admin/backup` - Trigger backup

## 🛠️ Tech Stack

- **Frontend:** HTML5, TailwindCSS, JavaScript
- **Backend:** Python, FastAPI
- **Database:** SQLite
- **AI:** Ollama (local LLM)
- **Deployment:** Docker

## 🌍 Localization

The platform supports:
- English (primary)
- Spanish (Español)

## 📄 License

Proprietary - Ometeolt / SCORPION AI Systems

---

Built with 🦂 in El Salvador | **Pay to USE and OWN at the same time**
