# J3 Interior Design - Deployment Guide for Debian Xibalba

## Quick Reference

| Component | Status | Location |
|-----------|--------|----------|
| Backend API | ✅ WORKING | `backend/` |
| Startup Script | ✅ WORKING | `start_backend.sh` |
| Dashboard | ⚠️ Needs config | `dashboard/` |
| WordPress Theme | ⚠️ Needs config | `wordpress/` |
| Docker Stack | ⚠️ Not tested | `docker/` |
| AI Chatbot | ⚠️ Basic | `ai_chatbot/` |

---

## What You Have Built

### ✅ FULLY FUNCTIONAL (Tested and Ready)

#### 1. Backend API Server (Flask)
**Location:** `backend/`
**Status:** TESTED AND WORKING

Features:
- Real Houston zip code database (100+ zips with distance)
- Budget parsing (handles $50k, 50000, 50k-100k, etc.)
- JSON persistence (leads survive restarts)
- Lead scoring (0-100 points with 5 priority levels)
- REST API endpoints for all operations

API Endpoints:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/leads` | POST | Create new lead |
| `/api/leads` | GET | List all leads |
| `/api/leads/<id>` | GET | Get single lead |
| `/api/leads/<id>/status` | PUT | Update lead status |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/api/chat` | POST | Chat endpoint |

#### 2. Startup Script
**Location:** `start_backend.sh`
**Status:** TESTED AND WORKING

```bash
./start_backend.sh        # Development mode (Flask debug)
./start_backend.sh prod   # Production mode (Gunicorn)
```

#### 3. Commander Dashboard
**Location:** `dashboard/index.html`
**Status:** HTML/CSS COMPLETE

Features:
- Lead overview cards
- Priority filtering
- Pipeline value display
- Recent leads table

### ⚠️ NEEDS CONFIGURATION

#### 1. WordPress Frontend
**Location:** `wordpress/wp-content/themes/j3-interior-pro/`

Needs:
- Update API URL in `js/main.js` (line ~15)
- Change: `apiBaseUrl: '/api'` to `apiBaseUrl: 'http://YOUR_SERVER:5000/api'`

#### 2. Docker Stack
**Location:** `docker/`

Needs:
- Copy `.env.example` to `.env`
- Fill in passwords and API keys
- Test deployment

#### 3. AI Chatbot
**Location:** `ai_chatbot/`

Needs:
- Connect to your Ollama instance
- Configure model endpoint

### ❌ NEEDS MANUAL SETUP

1. **Stripe Payment Processing** - Requires API keys from stripe.com
2. **Google Calendar Integration** - Requires OAuth setup in Google Cloud Console
3. **Twilio SMS Notifications** - Requires Twilio account and keys

---

## Quick Start - Backend Only (5 minutes)

```bash
# 1. Navigate to the project
cd /home/user/hello-world

# 2. Start the backend
./start_backend.sh

# 3. Test health check
curl http://localhost:5000/api/health

# Expected output:
# {"service":"J3 Interior Design API","status":"healthy","timestamp":"...","version":"1.0.0"}

# 4. Submit a test lead
curl -X POST http://localhost:5000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Customer",
    "email": "test@example.com",
    "phone": "713-555-1234",
    "zip": "77002",
    "project_type": "kitchen",
    "budget": "40k",
    "timeline": "asap",
    "description": "Need kitchen remodel"
  }'

# 5. Check dashboard stats
curl http://localhost:5000/api/dashboard/stats

# 6. View all leads
curl http://localhost:5000/api/leads
```

---

## Deploy to Debian Xibalba Fortress

### Prerequisites
- Python 3.8+ installed
- pip installed
- Git installed (optional, for pulling updates)

### Step 1: Transfer Files to Xibalba

**Option A: Git Clone (Recommended)**
```bash
# On Xibalba
cd ~
git clone https://github.com/Charliesonlineclass/hello-world.git
cd hello-world
git checkout claude/j3-interior-design-system-011FKBZsgq1NcVyaWq8fdRv2
```

**Option B: SCP Transfer**
```bash
# From cloud environment (or wherever files are)
scp -r /home/user/hello-world user@xibalba:~/

# On Xibalba
cd ~/hello-world
```

**Option C: USB Drive**
```bash
# Copy to USB
cp -r /home/user/hello-world /media/usb/

# On Xibalba, copy from USB
cp -r /media/usb/hello-world ~/
cd ~/hello-world
```

### Step 2: Move to ScorpionKing Fortress
```bash
# Create directory structure
mkdir -p ~/ScorpionKing/CentaurHQ/j3_interior

# Copy project files
cp -r ~/hello-world/* ~/ScorpionKing/CentaurHQ/j3_interior/

# Navigate there
cd ~/ScorpionKing/CentaurHQ/j3_interior
```

### Step 3: Configure Environment
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask flask-cors gunicorn requests

# Create data directory
mkdir -p data
```

### Step 4: Run Backend
```bash
# Development mode (for testing)
./start_backend.sh

# OR Production mode (for real use)
./start_backend.sh prod
```

Backend now running on port 5000.

### Step 5: Test the API
```bash
# Health check
curl http://localhost:5000/api/health

# Create a test lead
curl -X POST http://localhost:5000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "713-555-1234",
    "zip": "77002",
    "project_type": "kitchen",
    "budget": "50k",
    "timeline": "asap",
    "description": "Complete kitchen renovation"
  }'

# View leads
curl http://localhost:5000/api/leads
```

### Step 6: Access Dashboard
```bash
# Option A: Open directly in browser
firefox dashboard/index.html &

# Option B: Copy to web server
sudo cp dashboard/index.html /var/www/html/j3-dashboard.html
# Then visit: http://localhost/j3-dashboard.html

# Option C: Python simple server
cd dashboard
python3 -m http.server 8080 &
# Then visit: http://localhost:8080/index.html
```

### Step 7: Configure Dashboard API URL
Edit `dashboard/index.html`, find this line (around line 50):
```javascript
const API_BASE = 'http://localhost:5000';
```
Change to your server's IP if accessing remotely:
```javascript
const API_BASE = 'http://192.168.1.100:5000';  // Your Xibalba IP
```

---

## Run as Background Service

### Option 1: Screen (Simple)
```bash
# Start in screen session
screen -S j3backend
cd ~/ScorpionKing/CentaurHQ/j3_interior
./start_backend.sh prod

# Detach: Ctrl+A, then D
# Reattach: screen -r j3backend
```

### Option 2: Systemd Service (Production)
```bash
# Create service file
sudo nano /etc/systemd/system/j3-backend.service
```

Paste this content:
```ini
[Unit]
Description=J3 Interior Design Backend API
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/ScorpionKing/CentaurHQ/j3_interior/backend
ExecStart=/home/YOUR_USERNAME/ScorpionKing/CentaurHQ/j3_interior/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable j3-backend
sudo systemctl start j3-backend

# Check status
sudo systemctl status j3-backend

# View logs
sudo journalctl -u j3-backend -f
```

---

## Docker Deployment (When Ready)

### Step 1: Install Docker
```bash
# Debian
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
# Log out and back in
```

### Step 2: Configure Environment
```bash
cd docker
cp .env.example .env
nano .env
```

Fill in these values:
```bash
# Database
MYSQL_ROOT_PASSWORD=your_strong_password_here
MYSQL_PASSWORD=another_strong_password

# WordPress
WORDPRESS_DB_PASSWORD=same_as_mysql_password

# API Keys (when you have them)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
```

### Step 3: Start Stack
```bash
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

Services will be available at:
- WordPress: http://localhost:80
- Backend API: http://localhost:5000
- Dashboard: http://localhost:8080

---

## What Works Right Now

| Feature | Status | Test Command |
|---------|--------|--------------|
| Health check | ✅ | `curl http://localhost:5000/api/health` |
| Create lead | ✅ | `curl -X POST http://localhost:5000/api/leads -H "Content-Type: application/json" -d '{...}'` |
| List leads | ✅ | `curl http://localhost:5000/api/leads` |
| Dashboard stats | ✅ | `curl http://localhost:5000/api/dashboard/stats` |
| Lead persistence | ✅ | Restart server, leads still there |
| Geographic scoring | ✅ | Houston zips get high scores |
| Budget parsing | ✅ | 50k, $50,000, 50k-100k all work |
| Priority routing | ✅ | HOT/WARM/LUKEWARM/COLD/DISQUALIFIED |

---

## Testing Checklist

- [ ] Python 3.8+ installed: `python3 --version`
- [ ] Backend starts without errors: `./start_backend.sh`
- [ ] Health check returns "healthy": `curl http://localhost:5000/api/health`
- [ ] Can create a lead via curl
- [ ] Lead appears in leads list
- [ ] Dashboard stats update correctly
- [ ] Leads persist after backend restart
- [ ] Dashboard displays in browser

---

## Troubleshooting

### Backend Won't Start
```bash
# Check Python version (need 3.7+)
python3 --version

# Install dependencies manually
cd backend
source venv/bin/activate
pip install flask flask-cors gunicorn

# Check for port conflict
netstat -tlnp | grep 5000
# Kill conflicting process if needed
```

### Leads Not Persisting
```bash
# Check data directory exists
cd backend
ls -la data/

# Check file permissions
chmod 755 data/
chmod 644 data/leads.json  # If file exists
```

### Can't Connect from Browser
```bash
# Check if backend is running
ps aux | grep api_server

# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp  # If needed

# Check what's listening
netstat -tlnp | grep 5000
```

### CORS Errors in Browser
The backend has CORS enabled. If you still get CORS errors:
1. Check the browser console for the exact error
2. Ensure you're using the correct API URL
3. Try accessing the API directly (curl) to verify it works

---

## File Structure

```
hello-world/
├── backend/
│   ├── api_server.py        # Flask API (WORKING)
│   ├── lead_qualifier.py    # Scoring algorithm (WORKING)
│   ├── requirements.txt     # Python dependencies
│   ├── venv/                # Virtual environment (auto-created)
│   └── data/                # Leads stored here (auto-created)
│       └── leads.json       # Lead data file
├── dashboard/
│   └── index.html           # Commander dashboard
├── wordpress/
│   └── wp-content/themes/j3-interior-pro/
│       ├── index.html       # Homepage
│       ├── style.css        # Styling
│       └── js/main.js       # Frontend logic
├── docker/
│   ├── docker-compose.yml   # Full stack config
│   ├── .env.example         # Environment template
│   └── Dockerfile.backend   # Backend container
├── ai_chatbot/
│   └── chatbot.py           # AI chat (basic)
├── start_backend.sh         # One-command startup (WORKING)
├── .gitignore               # Git ignore rules
├── README.md                # Project overview
└── DEPLOYMENT_GUIDE.md      # This file
```

---

## Production Recommendations

1. **Use Gunicorn** for production: `./start_backend.sh prod`
2. **Set up Nginx** reverse proxy for HTTPS
3. **Configure firewall** to only expose necessary ports
4. **Regular backups** of `backend/data/leads.json`
5. **Monitor logs** - backend has logging enabled
6. **Strong passwords** in all config files
7. **Never commit `.env`** files to git

---

## Integration Roadmap

### Phase 1: Backend Only (NOW)
- ✅ Lead qualification API working
- ✅ Geographic scoring with Houston zips
- ✅ Budget parsing for multiple formats
- ✅ JSON persistence

### Phase 2: Dashboard Integration
- [ ] Connect dashboard to API
- [ ] Add real-time updates
- [ ] Add lead management actions

### Phase 3: Frontend Integration
- [ ] Connect WordPress form to API
- [ ] Add chat widget
- [ ] Style confirmation messages

### Phase 4: Advanced Features
- [ ] Stripe payment integration
- [ ] Google Calendar scheduling
- [ ] SMS notifications via Twilio
- [ ] Enhanced AI chatbot with Ollama

---

## Support

For issues:
- Check this guide's troubleshooting section
- Review logs: `journalctl -u j3-backend -f` (if using systemd)
- Check backend console output

Files location on Xibalba:
```
~/ScorpionKing/CentaurHQ/j3_interior/
```

Backup your leads regularly:
```bash
cp ~/ScorpionKing/CentaurHQ/j3_interior/backend/data/leads.json ~/backups/leads_$(date +%Y%m%d).json
```
