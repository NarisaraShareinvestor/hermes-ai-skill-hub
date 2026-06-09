# 🐳 Docker Deployment on Hostinger VPS

Quick deployment guide using Docker Compose on Hostinger

---

## 📋 Prerequisites

- [ ] Hostinger VPS account (with SSH access)
- [ ] Domain name (or subdomain)
- [ ] API Keys ready:
  - Anthropic API Key
  - Telegram Bot Token
  - OpenAI API Key (optional)

---

## 🚀 Step-by-Step Deployment

### **Step 1: Connect to Hostinger VPS**

```bash
ssh root@your_vps_ip
# or
ssh username@your_vps_ip
```

### **Step 2: Update System**

```bash
apt update && apt upgrade -y
```

### **Step 3: Install Docker**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### **Step 4: Clone Repository**

```bash
cd /var/www
git clone https://github.com/narisarapaewpairee/hermes-ai-skill-hub.git
cd hermes-ai-skill-hub
```

### **Step 5: Configure Environment**

```bash
# Copy production env template
cp .env.production .env.production.local

# Edit with your values
nano .env.production.local
```

**必填 fields to update:**
```env
DOMAIN_NAME=your-domain.com
DATABASE_URL=postgresql://hermes_user:STRONG_PASSWORD@postgres:5432/hermes_db
DB_PASSWORD=STRONG_PASSWORD
ANTHROPIC_API_KEY=sk-ant-...your-key...
TELEGRAM_BOT_TOKEN=...your-token...
SECRET_KEY=...generate-strong-key...
REDIS_PASSWORD=STRONG_PASSWORD
```

### **Step 6: Generate SSL Certificate**

#### Option A: Using Let's Encrypt (Recommended)

```bash
# Install Certbot
apt install -y certbot python3-certbot-dns-cloudflare

# Get certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Create ssl directory
mkdir -p ssl

# Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/

# Set permissions
chmod 644 ssl/fullchain.pem
chmod 644 ssl/privkey.pem
```

#### Option B: Self-signed Certificate (Development only)

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes -out ssl/fullchain.pem -keyout ssl/privkey.pem -days 365
```

### **Step 7: Create Docker Network & Volumes**

```bash
docker network create hermes_network

# Create directories for data
mkdir -p backups
mkdir -p backend/uploads
```

### **Step 8: Start Docker Containers**

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml --env-file .env.production.local up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### **Step 9: Verify Deployment**

```bash
# Check backend health
curl http://127.0.0.1:8000/docs

# Check database connection
docker-compose -f docker-compose.prod.yml exec postgres psql -U hermes_user -d hermes_db -c "SELECT 1"

# Check Nginx
curl http://127.0.0.1/health
```

### **Step 10: Access Application**

Open browser and go to:
```
https://your-domain.com/app.html
```

---

## 🔄 Auto-renewal SSL Certificate

```bash
# Create renewal script
nano /usr/local/bin/renew-certs.sh
```

Add:
```bash
#!/bin/bash
certbot renew --quiet
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /var/www/hermes-ai-skill-hub/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem /var/www/hermes-ai-skill-hub/ssl/
docker-compose -f /var/www/hermes-ai-skill-hub/docker-compose.prod.yml reload
```

Make executable:
```bash
chmod +x /usr/local/bin/renew-certs.sh
```

Add to crontab:
```bash
crontab -e
# Add: 0 3 * * * /usr/local/bin/renew-certs.sh
```

---

## 📊 Common Docker Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Enter container
docker-compose -f docker-compose.prod.yml exec backend bash

# Restart service
docker-compose -f docker-compose.prod.yml restart backend

# Stop all
docker-compose -f docker-compose.prod.yml down

# Rebuild images
docker-compose -f docker-compose.prod.yml build --no-cache

# Prune unused images
docker image prune -a -f
```

---

## 🗄️ Database Backup & Restore

### Backup

```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U hermes_user -d hermes_db > backups/hermes_backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backups/hermes_backup_*.sql
```

### Scheduled Backup (Cron)

```bash
# Create backup script
nano /usr/local/bin/backup-hermes.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/var/www/hermes-ai-skill-hub/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

cd /var/www/hermes-ai-skill-hub

# Backup
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U hermes_user -d hermes_db | gzip > ${BACKUP_DIR}/hermes_${TIMESTAMP}.sql.gz

# Keep only last 30 days
find ${BACKUP_DIR} -name "hermes_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
# aws s3 cp ${BACKUP_DIR}/hermes_${TIMESTAMP}.sql.gz s3://your-bucket/backups/
```

Make executable and add to cron:
```bash
chmod +x /usr/local/bin/backup-hermes.sh
crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-hermes.sh
```

### Restore

```bash
# Restore from backup
gunzip backups/hermes_backup_YYYYMMDD_HHMMSS.sql.gz
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U hermes_user -d hermes_db < backups/hermes_backup_YYYYMMDD_HHMMSS.sql
```

---

## 🔒 Security Checklist

- [ ] Changed all default passwords in `.env.production.local`
- [ ] Generated strong `SECRET_KEY`
- [ ] Set proper file permissions: `chmod 600 .env.production.local`
- [ ] Enabled UFW firewall
- [ ] Installed Let's Encrypt SSL certificate
- [ ] Set up backup schedule
- [ ] Disabled SSH password login (use keys)
- [ ] Enabled HSTS in Nginx
- [ ] Removed debug mode (`DEBUG=False`)

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused` | Check if containers are running: `docker ps` |
| `Database connection error` | Verify `.env.production.local` DATABASE_URL |
| `SSL certificate not found` | Check ssl/ directory has fullchain.pem and privkey.pem |
| `502 Bad Gateway` | Check backend logs: `docker-compose logs backend` |
| `Out of memory` | Increase VPS RAM or add swap space |
| `Disk space full` | Check: `df -h` and prune Docker: `docker system prune -a` |

---

## 📞 Useful Links

- Docker Docs: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Hostinger Support: https://support.hostinger.com/
- FastAPI: https://fastapi.tiangolo.com/
- Let's Encrypt: https://letsencrypt.org/

---

**Deployment completed!** 🎉

Your app is now running at `https://your-domain.com/app.html`

Monitor with:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```
