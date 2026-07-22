#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# LinkedIn Job Scraper — EC2 Deployment Script
# ═══════════════════════════════════════════════════════════
# Run this script ON the EC2 instance after first SSH login.
#   ssh -i your-key.pem ec2-user@<ec2-public-ip>
#   bash deploy_ec2.sh
# ═══════════════════════════════════════════════════════════

set -euo pipefail

# ── Colors ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Pre-flight Checks ─────────────────────────────────────
log_info "Starting deployment..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please run as ec2-user (not root)"
    exit 1
fi

# Check for required env variables
if [ ! -f .env ]; then
    log_error ".env file not found! Create it first:"
    echo "  cp .env.example .env && nano .env"
    exit 1
fi

source .env

# ── Step 1: System Dependencies ───────────────────────────
log_info "Updating system packages..."
sudo yum update -y

log_info "Installing Docker & Git..."
sudo yum install -y docker git

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add ec2-user to docker group
sudo usermod -aG docker ec2-user

log_ok "Docker installed successfully"

# ── Step 2: Clone / Pull Repository ───────────────────────
REPO_DIR="/home/ec2-user/linkedin-job-scraper"

if [ -d "$REPO_DIR" ]; then
    log_info "Repository exists — pulling latest changes..."
    cd "$REPO_DIR"
    git pull origin main
else
    log_info "Cloning repository..."
    # Replace with YOUR GitHub repo URL
    GIT_REPO_URL="${GIT_REPO_URL:-https://github.com/YOUR_USERNAME/linkedin-job-scraper.git}"
    git clone "$GIT_REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Copy .env to the cloned directory (preserve secrets)
log_info "Configuring environment..."
if [ -f /home/ec2-user/.env ]; then
    cp /home/ec2-user/.env "$REPO_DIR/.env"
    log_ok ".env file placed correctly"
fi

# ── Step 3: Build & Run Docker Container ──────────────────
log_info "Building Docker image..."
cd "$REPO_DIR"

# Stop and remove old container if exists
docker stop linkedin-scraper 2>/dev/null || true
docker rm linkedin-scraper 2>/dev/null || true

# Build fresh image
docker build -t linkedin-scraper:latest .

log_info "Starting container..."
docker run -d \
    --name linkedin-scraper \
    --restart unless-stopped \
    -p 8000:8000 \
    --env-file .env \
    linkedin-scraper:latest

log_ok "Docker container is running!"

# ── Step 4: Health Check ──────────────────────────────────
log_info "Running health check (waiting 10s)..."
sleep 10

HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    log_ok "Backend API is healthy! (HTTP 200)"
else
    log_warn "Health check returned HTTP $HEALTH_STATUS — checking logs..."
    docker logs linkedin-scraper --tail 20
fi

# ── Step 5: Install Nginx (Optional) ──────────────────────
if [ "${INSTALL_NGINX:-true}" = "true" ]; then
    log_info "Setting up Nginx reverse proxy..."

    sudo yum install -y nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx

    # Copy nginx config
    sudo cp "$REPO_DIR/nginx.conf" /etc/nginx/nginx.conf

    # Replace placeholder server_name with EC2 public IP
    EC2_IP=$(curl -s http://checkip.amazonaws.com || echo "localhost")
    sudo sed -i "s/server_name _;/server_name $EC2_IP;/g" /etc/nginx/nginx.conf

    # Test and reload
    sudo nginx -t && sudo systemctl reload nginx
    log_ok "Nginx configured and running!"
fi

# ── Summary ───────────────────────────────────────────────
EC2_IP=$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo "localhost")

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║           DEPLOYMENT COMPLETE                    ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  API URL:    http://${EC2_IP}:8000             ║"
echo "║  Health:     http://${EC2_IP}:8000/api/health  ║"
echo "║  Docs:       http://${EC2_IP}:8000/docs         ║"
echo "║                                                   ║"
echo "║  Docker:     linkedin-scraper (port 8000)        ║"
echo "║  Nginx:      Port 80 → FastAPI:8000              ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
log_info "Don't forget to:"
echo "  1. Point your Vercel frontend to: http://${EC2_IP}:8000"
echo "     (Set NEXT_PUBLIC_API_BASE_URL in Vercel env vars)"
echo ""
echo "  2. Update ALLOWED_ORIGINS in .env if using custom domain"
echo ""

