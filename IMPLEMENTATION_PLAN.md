# 🚀 LinkedIn Job Scraper — Complete Deployment Plan

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                           VERCEL (Frontend)                         │
│                    https://your-app.vercel.app                      │
│                          Next.js 16 + Turbopack                     │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ HTTPS / API Calls
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      AWS EC2 t2.micro (Backend)                     │
│                    http://<ec2-public-ip>:8000                      │
│  ┌──────────┐    ┌──────────────────┐    ┌──────────────────────┐   │
│  │  Nginx   │───▶│  FastAPI/Uvicorn  │───▶│  Docker Container    │   │
│  │  :80     │    │  :8000            │    │  (Python 3.12)       │   │
│  └──────────┘    └──────────────────┘    └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      NEON POSTGRESQL (Database)                      │
│                    postgresql://...ep-xxx.neon.tech                  │
│                           FREE Tier (5GB)                           │
│                        Serverless + SSL                             │
└──────────────────────────────────────────────────────────────────────┘
                           ▲
                           │
┌──────────────────────────────────────────────────────────────────────┐
│                         APIFY (Scraping)                             │
│                     External API Service                             │
└──────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

| # | Item | How to Get | Cost |
|---|------|------------|------|
| 1 | **GitHub Repository** | Already have it ✅ | Free |
| 2 | **AWS Account** | Already have it ✅ | Free (12 months) |
| 3 | **Neon PostgreSQL** | https://neon.tech → Sign up → Create project | Free (5GB) |
| 4 | **Apify Account** | https://apify.com → Get API token | Free tier |
| 5 | **Vercel Account** | https://vercel.com → Sign up with GitHub | Free |

## Step-by-Step Deployment

### Phase 1: Database — Neon PostgreSQL

```bash
# 1. Go to https://neon.tech
# 2. Sign up (GitHub OAuth recommended)
# 3. Create a new project → name: "linkedin-scraper"
# 4. Region: US East (us-east-1) — same as EC2 for low latency
# 5. Wait 10-15 seconds for provisioning
# 6. Copy the DATABASE_URL from "Connection Details"
#    It looks like:
#    postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/linkedin_jobs?sslmode=require
```

### Phase 2: Backend — AWS EC2

#### Step 1: Create EC2 Instance (via AWS Console)

| Setting | Value |
|---------|-------|
| Name | `linkedin-scraper` |
| AMI | Amazon Linux 2 (free tier eligible) |
| Instance Type | `t2.micro` (free tier) |
| Key Pair | Create new: `linkedin-scraper-key` |
| Network | Default VPC |
| Security Group | Create new with rules below |
| Storage | 20 GB gp3 (free tier) |

**Security Group Rules:**

| Type | Protocol | Port | Source |
|------|----------|------|--------|
| SSH | TCP | 22 | 0.0.0.0/0 |
| HTTP | TCP | 80 | 0.0.0.0/0 |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 |

#### Step 2: SSH into EC2 & Deploy

```bash
# SSH into your instance
ssh -i linkedin-scraper-key.pem ec2-user@<ec2-public-ip>

# Update system
sudo yum update -y
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Logout and log back in for docker group to take effect
exit
ssh -i linkedin-scraper-key.pem ec2-user@<ec2-public-ip>

# Clone repository
git clone https://github.com/YOUR_USERNAME/linkedin-job-scraper.git
cd linkedin-job-scraper

# Create .env file
cat > .env << 'ENVEOF'
# ── Apify ──
APIFY_TOKEN=your_apify_token_here
APIFY_ACTOR_ID=apify/linkedin-jobs-scraper

# ── Database (Neon) ──
DATABASE_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/linkedin_jobs?sslmode=require

# ── Backend Config ──
MAX_RESULTS=100
SCHEDULE_INTERVAL=60
SCRAPER_ENABLED=True
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app
LOG_LEVEL=INFO
ENVEOF

# Build and run Docker container
docker build -t linkedin-scraper:latest .
docker run -d \
    --name linkedin-scraper \
    --restart unless-stopped \
    -p 8000:8000 \
    --env-file .env \
    linkedin-scraper:latest

# Verify health
sleep 5
curl http://localhost:8000/api/health
```

**Expected response:**
```json
{"success":true,"data":{"status":"healthy","database":"connected","timestamp":"..."}}
```

#### Step 3: (Optional) Nginx Reverse Proxy

```bash
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Get your EC2 public IP
EC2_IP=$(curl -s http://checkip.amazonaws.com)

# Configure nginx
sudo tee /etc/nginx/nginx.conf > /dev/null << 'NGINXCONF'
events {}
http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server {
        listen 80;
        server_name EC2_IP;

        client_max_body_size 20M;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 120s;
            proxy_connect_timeout 120s;
            proxy_send_timeout 120s;
        }

        location /health {
            proxy_pass http://127.0.0.1:8000/api/health;
            access_log off;
        }
    }
}
NGINXCONF

# Replace placeholder with actual IP
sudo sed -i "s/EC2_IP/$EC2_IP/g" /etc/nginx/nginx.conf

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
```

### Phase 3: Frontend — Vercel Deployment

#### Option A: Deploy via Vercel Dashboard (Recommended)

```bash
# 1. Go to https://vercel.com
# 2. Click "Add New" → "Project"
# 3. Import your GitHub repository
# 4. Configure:
#    - Framework Preset: Next.js
#    - Root Directory: frontend/  ← IMPORTANT
#    - Build Command: npm run build
#    - Output Directory: .next
# 5. Add Environment Variables:
#    NEXT_PUBLIC_API_BASE_URL = http://<ec2-public-ip>:8000
#    (or http://<ec2-public-ip> if using nginx on port 80)
# 6. Click "Deploy"
```

#### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from frontend directory
cd frontend
vercel --prod \
    --env NEXT_PUBLIC_API_BASE_URL=http://<ec2-public-ip>:8000
```

### Phase 4: Verify Everything

```bash
# 1. Test Backend Health
curl http://<ec2-public-ip>:8000/api/health

# 2. Test API Endpoints
curl http://<ec2-public-ip>:8000/api/jobs?limit=5
curl http://<ec2-public-ip>:8000/api/statistics

# 3. Open Frontend
open https://your-app.vercel.app

# 4. Test Scraping
curl -X POST http://<ec2-public-ip>:8000/api/jobs/scrape \
    -H "Content-Type: application/json" \
    -d '{"keyword":"Python","location":"Remote","max_results":10}'
```

## Environment Variables Reference

### Backend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APIFY_TOKEN` | ✅ Yes | - | Apify API token for scraping |
| `APIFY_ACTOR_ID` | ✅ No | `apify/linkedin-jobs-scraper` | Apify actor ID |
| `DATABASE_URL` | ✅ Yes | - | Neon PostgreSQL connection string |
| `POSTGRES_HOST` | ❌ No | `localhost` | Fallback if DATABASE_URL not set |
| `POSTGRES_PORT` | ❌ No | `5432` | Postgres port |
| `POSTGRES_DB` | ❌ No | `linkedin_jobs` | Database name |
| `POSTGRES_USER` | ❌ No | `postgres` | DB user |
| `POSTGRES_PASSWORD` | ❌ No | `postgres` | DB password |
| `MAX_RESULTS` | ❌ No | `100` | Max jobs per scrape |
| `SCHEDULE_INTERVAL` | ❌ No | `60` | Scheduler interval (minutes) |
| `SCRAPER_ENABLED` | ❌ No | `True` | Enable background scheduler |
| `ALLOWED_ORIGINS` | ❌ No | `http://localhost:3000` | CORS origins (comma-separated) |
| `LOG_LEVEL` | ❌ No | `INFO` | Logging level |

### Frontend (.env.local / Vercel)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | ✅ Yes | `http://127.0.0.1:8000` | Backend API URL |

## Troubleshooting

### Issue: "Connection refused" on EC2
```bash
# Check if Docker is running
docker ps

# Check container logs
docker logs linkedin-scraper

# Check if port is open
sudo netstat -tlnp | grep 8000

# Check EC2 Security Group — ensure port 8000 is open
```

### Issue: "SSL required" from Neon
```bash
# Ensure DATABASE_URL ends with ?sslmode=require
# The database.py already handles this automatically
```

### Issue: Frontend shows "Network Error"
```bash
# 1. Check CORS in .env:
#    ALLOWED_ORIGINS should include your Vercel domain
#    e.g., ALLOWED_ORIGINS=https://your-app.vercel.app

# 2. Restart Docker container after .env change:
docker stop linkedin-scraper
docker rm linkedin-scraper
docker run -d --name linkedin-scraper --restart unless-stopped -p 8000:8000 --env-file .env linkedin-scraper:latest
```

### Issue: Apify token invalid
```bash
# Verify your token
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.apify.com/v2/me

# Expected: 200 OK with your user info
```

## Cost Summary (First 12 Months)

| Service | Plan | Monthly Cost | Annual Cost |
|---------|------|--------------|-------------|
| AWS EC2 t2.micro | Free Tier | $0 | $0 |
| Neon PostgreSQL | Free (5GB) | $0 | $0 |
| Vercel | Hobby | $0 | $0 |
| Apify | Free ($5 credit) | $0 | $0 |
| **TOTAL** | | **$0** | **$0** |

After 12 months, EC2 costs ~$8.50/month. Consider switching to a smaller instance or using AWS Lambda for further cost optimization.

## Quick Commands Reference

```bash
# Local Development
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # Windows
pip install -r requirements.txt
python main.py                   # Run scraper once
python -m uvicorn app.main_api:app --reload --port 8000  # API server

# Frontend
cd frontend && npm install && npm run dev

# EC2 Management
docker start linkedin-scraper
docker stop linkedin-scraper
docker logs -f linkedin-scraper
docker restart linkedin-scraper
```

