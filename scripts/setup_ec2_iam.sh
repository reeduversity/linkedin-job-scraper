#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# LinkedIn Job Scraper — EC2 Instance Setup (Run Locally)
# ═══════════════════════════════════════════════════════════
# Run this on YOUR LOCAL MACHINE to configure AWS CLI
# and create the EC2 instance + security group.
# ═══════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuration (Edit these!) ───────────────────────────
STACK_NAME="linkedin-scraper"
INSTANCE_TYPE="t2.micro"
REGION="us-east-1"  # Change to your preferred region
AMI_ID="ami-0c55b159cbfafe1f0"  # Amazon Linux 2 (us-east-1)
KEY_NAME="linkedin-scraper-key"  # Will be created
# ──────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()     { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn(){ echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Check Prerequisites ───────────────────────────────────
log "Checking prerequisites..."

command -v aws >/dev/null 2>&1 || error "AWS CLI not installed. Install it first: https://aws.amazon.com/cli/"
command -v jq  >/dev/null 2>&1 || error "jq not found. Install: sudo apt-get install jq (or brew install jq)"

# Verify AWS credentials
aws sts get-caller-identity --output json >/dev/null 2>&1 || error "AWS CLI not configured. Run: aws configure"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log "AWS Account: $ACCOUNT_ID"
log "Region:      $REGION"

# ── Step 1: Create Key Pair ───────────────────────────────
log "Creating EC2 key pair..."
if [ ! -f "${KEY_NAME}.pem" ]; then
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' \
        --output text > "${KEY_NAME}.pem"
    chmod 400 "${KEY_NAME}.pem"
    log "Key pair created: ${KEY_NAME}.pem"
else
    log_warn "Key file ${KEY_NAME}.pem already exists — using it"
fi

# ── Step 2: Create Security Group ─────────────────────────--
log "Creating security group..."

SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${STACK_NAME}-sg" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
    SG_ID=$(aws ec2 create-security-group \
        --group-name "${STACK_NAME}-sg" \
        --description "Security group for LinkedIn Job Scraper" \
        --query 'GroupId' \
        --output text)
    log "Security group created: $SG_ID"
else
    log_warn "Security group already exists: $SG_ID"
fi

# ── Step 3: Configure Security Group Rules ────────────────
log "Configuring security group rules..."

# SSH access
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 22 \
    --cidr "0.0.0.0/0" 2>/dev/null || log_warn "SSH rule already exists"

# HTTP access (Nginx)
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 80 \
    --cidr "0.0.0.0/0" 2>/dev/null || log_warn "HTTP rule already exists"

# Backend API access
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 8000 \
    --cidr "0.0.0.0/0" 2>/dev/null || log_warn "API rule already exists"

log "Security group rules configured:"
aws ec2 describe-security-groups \
    --group-ids "$SG_ID" \
    --query 'SecurityGroups[0].IpPermissions' \
    --output table

# ── Step 4: Launch EC2 Instance ───────────────────────────--
log "Launching EC2 instance..."

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --associate-public-ip-address \
    --block-device-mappings "[{\"DeviceName\":\"/dev/xvda\",\"Ebs\":{\"VolumeSize\":20,\"VolumeType\":\"gp3\"}}]" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${STACK_NAME}}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

log "Instance launched: $INSTANCE_ID"

# ── Step 5: Wait for Instance to be Ready ────────────────
log "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

log "Instance ready!"
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║              EC2 INSTANCE CREATED                ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Instance ID:  $INSTANCE_ID "
echo "║  Public IP:    $PUBLIC_IP"
echo "║  SSH Command:  ssh -i ${KEY_NAME}.pem ec2-user@${PUBLIC_IP}"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. SSH into the instance:"
echo "     ssh -i ${KEY_NAME}.pem ec2-user@${PUBLIC_IP}"
echo ""
echo "  2. Upload your .env file:"
echo "     scp -i ${KEY_NAME}.pem .env ec2-user@${PUBLIC_IP}:~/"
echo ""
echo "  3. Run the deployment script:"
echo "     bash deploy_ec2.sh"
echo ""
echo "  4. Set Vercel env var NEXT_PUBLIC_API_BASE_URL to:"
echo "     http://${PUBLIC_IP}:8000"
echo ""

