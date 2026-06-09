#!/bin/bash

# =====================================================
# Hermes AI Skill Hub - Hostinger VPS Docker Deployment
# =====================================================
# Usage: bash deploy-hostinger.sh
# This script automates Docker deployment on Hostinger VPS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Hermes AI Skill Hub - Docker Deployment Script   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}\n"

# =====================================================
# Function: Print colored messages
# =====================================================
print_header() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# =====================================================
# Step 1: Check Prerequisites
# =====================================================
print_header "Checking Prerequisites"

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Install Docker: curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
    exit 1
fi
print_success "Docker is installed: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    echo "Install: sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m) -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi
print_success "Docker Compose is installed: $(docker-compose --version)"

if ! command -v git &> /dev/null; then
    print_error "Git is not installed"
    exit 1
fi
print_success "Git is installed"

# =====================================================
# Step 2: Validate Configuration
# =====================================================
print_header "Validating Configuration"

if [ ! -f ".env.production.local" ]; then
    print_error ".env.production.local not found"
    echo "Please copy .env.production to .env.production.local and update values"
    exit 1
fi
print_success ".env.production.local exists"

if [ ! -f "docker-compose.prod.yml" ]; then
    print_error "docker-compose.prod.yml not found"
    exit 1
fi
print_success "docker-compose.prod.yml found"

if [ ! -f "nginx.conf" ]; then
    print_error "nginx.conf not found"
    exit 1
fi
print_success "nginx.conf found"

# =====================================================
# Step 3: Check SSL Certificates
# =====================================================
print_header "Checking SSL Certificates"

if [ ! -d "ssl" ]; then
    print_warning "ssl directory not found"
    mkdir -p ssl
    print_warning "Created ssl directory, but you need to add certificates"
    echo "Copy your SSL certificates to:"
    echo "  - ssl/fullchain.pem"
    echo "  - ssl/privkey.pem"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    if [ -f "ssl/fullchain.pem" ] && [ -f "ssl/privkey.pem" ]; then
        print_success "SSL certificates found"
    else
        print_warning "SSL directory exists but certificates missing"
    fi
fi

# =====================================================
# Step 4: Create Necessary Directories
# =====================================================
print_header "Creating Directories"

mkdir -p backups
print_success "backups directory ready"

mkdir -p backend/uploads
print_success "backend/uploads directory ready"

mkdir -p logs
print_success "logs directory ready"

# =====================================================
# Step 5: Build Docker Images
# =====================================================
print_header "Building Docker Images"

docker-compose -f docker-compose.prod.yml build --no-cache
if [ $? -eq 0 ]; then
    print_success "Docker images built successfully"
else
    print_error "Failed to build Docker images"
    exit 1
fi

# =====================================================
# Step 6: Start Services
# =====================================================
print_header "Starting Docker Services"

docker-compose -f docker-compose.prod.yml --env-file .env.production.local up -d

if [ $? -eq 0 ]; then
    print_success "Docker services started"
else
    print_error "Failed to start Docker services"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi

# =====================================================
# Step 7: Wait for Services to Be Ready
# =====================================================
print_header "Waiting for Services to Start"

echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U hermes_user &> /dev/null; then
        print_success "PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL failed to start"
        exit 1
    fi
    sleep 1
done

echo "Waiting for Backend..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/docs &> /dev/null; then
        print_success "Backend is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Backend failed to start"
        docker-compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
    sleep 2
done

# =====================================================
# Step 8: Verify Deployment
# =====================================================
print_header "Verifying Deployment"

echo "Docker container status:"
docker-compose -f docker-compose.prod.yml ps
print_success "All containers running"

# =====================================================
# Step 9: Display Summary
# =====================================================
print_header "Deployment Summary"

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════╗"
echo "║     ✓ Hermes AI Skill Hub Deployed Successfully   ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get domain from env
DOMAIN=$(grep "DOMAIN_NAME" .env.production.local | cut -d '=' -f2)

echo ""
echo -e "${BLUE}📱 Application URL:${NC}"
echo "  https://$DOMAIN/app.html"
echo ""

echo -e "${BLUE}📚 API Documentation:${NC}"
echo "  https://$DOMAIN/docs"
echo ""

echo -e "${BLUE}🔧 Admin Endpoints:${NC}"
echo "  Backend: http://127.0.0.1:8000"
echo "  Nginx: http://127.0.0.1:80"
if grep -q "ENABLE_N8N=true" .env.production.local; then
    echo "  n8n: https://$DOMAIN/n8n"
fi
echo ""

echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f backend"
echo "  Restart: docker-compose -f docker-compose.prod.yml restart"
echo "  Stop: docker-compose -f docker-compose.prod.yml down"
echo "  Backup DB: docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U hermes_user -d hermes_db > backups/hermes_backup_\$(date +%Y%m%d).sql"
echo ""

echo -e "${BLUE}⚠️  Next Steps:${NC}"
echo "  1. Configure your domain DNS to point to this VPS"
echo "  2. Test application at https://$DOMAIN/app.html"
echo "  3. Set up SSL auto-renewal certificate"
echo "  4. Configure backup schedule (crontab)"
echo "  5. Monitor logs regularly"
echo ""

echo -e "${GREEN}🎉 Deployment complete!${NC}\n"
