# J3 Interior Design Platform

Fortune 500 level interior design and remodeling business platform with AI-powered lead qualification, automated scheduling, and payment processing.

## Features

- **WordPress Frontend** - Professional, mobile-responsive website
- **Lead Qualification** - GroomBridge-style scoring algorithm (0-100 points)
- **AI Chatbot** - 24/7 lead engagement with local LLM
- **Appointment Scheduling** - Automated booking with Google Calendar
- **Payment Processing** - Stripe integration with deposit calculation
- **Commander Dashboard** - Real-time operations center

## Quick Start

```bash
cd docker
cp .env.example .env
docker-compose up -d
```

Access:
- Website: http://localhost:8080
- API: http://localhost:5000
- Dashboard: http://localhost:3000

## Lead Scoring

| Score | Priority | Response Time |
|-------|----------|---------------|
| 90-100 | HOT | 4 hours |
| 70-89 | WARM | 24 hours |
| 50-69 | LUKEWARM | 48 hours |
| 30-49 | COLD | Nurture |
| <30 | DISQUALIFIED | Polite rejection |

## Services (Houston + 120 mi radius)

- Kitchen Remodeling: $15,000 - $75,000+
- Bathroom Design: $8,000 - $35,000
- Flooring: $5,000 - $30,000
- Wall/Paint: $3,000 - $15,000
- Windows/Doors: $6,000 - $40,000
- Storm Restoration: Insurance billing

## API Endpoints

```
POST /api/leads - Create lead
GET /api/leads - List leads
GET /api/dashboard/stats - Dashboard data
POST /api/chat - AI chatbot
```

## Architecture

```
j3_interior/
├── wordpress/        # Frontend theme
├── backend/          # Flask API + lead scoring
├── ai_chatbot/       # Local LLM chatbot
├── dashboard/        # Operations dashboard
└── docker/           # Deployment config
```

---
Proprietary lead qualification algorithm. Commander earns 10% commission on closed deals.
