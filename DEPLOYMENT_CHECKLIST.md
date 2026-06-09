# 🚀 Deployment Checklist - Hermes AI Skill Hub

Quick reference guide for deploying to Hostinger VPS with Docker

---

## 📋 Pre-Deployment Checklist

### Account Setup
- [ ] Hostinger VPS account created
- [ ] SSH access enabled
- [ ] VPS OS: Ubuntu 20.04+ or CentOS 7+
- [ ] Root access or sudo privileges available

### Domain Setup
- [ ] Domain purchased or subdomain prepared
- [ ] Domain registrar accessible
- [ ] DNS management available

### API Keys Prepared
- [ ] Anthropic API Key (from console.anthropic.com)
- [ ] Telegram Bot Token (from @BotFather)
- [ ] OpenAI API Key (optional, from platform.openai.com)
- [ ] Strong database password ready
- [ ] Strong Redis password ready

---

## 🔧 Deployment Steps

### Step 1: SSH to Hostinger VPS

```bash
ssh root@your_vps_ip
```

- [ ] Successfully connected to VPS

### Step 2: Clone and Prepare Repository

```bash
cd /var/www
git clone https://github.com/narisarapaewpairee/hermes-ai-skill-hub.git
cd hermes-ai-skill-hub
```

- [ ] Repository cloned successfully

### Step 3: Configure Environment

```bash
cp .env.production .env.production.local
nano .env.production.local
```

**Update these fields:**
```
DOMAIN_NAME=your-domain.com
DATABASE_URL=postgresql://hermes_user:STRONG_PASSWORD@postgres:5432/hermes_db
DB_PASSWORD=STRONG_PASSWORD
ANTHROPIC_API_KEY=sk-ant-your-key
TELEGRAM_BOT_TOKEN=your-bot-token
SECRET_KEY=your-secret-key
REDIS_PASSWORD=STRONG_PASSWORD
```

- [ ] All required fields filled in `.env.production.local`
- [ ] `.env.production.local` permissions: `chmod 600 .env.production.local`

### Step 4: Install Docker & Docker Compose

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker-compose --version`

### Step 5: Set Up SSL Certificate

#### Option A: Let's Encrypt (Recommended)

```bash
apt install -y certbot python3-certbot-dns-cloudflare

sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

mkdir -p ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
chmod 644 ssl/*
```

- [ ] SSL certificate obtained
- [ ] Certificates copied to `ssl/` directory

#### Option B: Self-signed (Development Only)

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes -out ssl/fullchain.pem -keyout ssl/privkey.pem -days 365
```

- [ ] Self-signed certificates created

### Step 6: Run Deployment Script

```bash
bash deploy-hostinger.sh
```

- [ ] Deployment script completed successfully
- [ ] All Docker containers running

### Step 7: Configure Domain DNS

In your domain registrar:

- [ ] Set A record pointing to VPS IP
- [ ] Set CNAME `www` record (optional)
- [ ] Wait for DNS propagation (5-30 minutes)

```bash
# Test DNS resolution
nslookup your-domain.com
```

- [ ] DNS records pointing to VPS
- [ ] DNS propagation complete

### Step 8: Verify Application

```bash
# Check containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Test endpoints
curl https://your-domain.com/health
curl https://your-domain.com/docs
```

- [ ] Access https://your-domain.com/app.html in browser
- [ ] Login page loads successfully
- [ ] API endpoints responding

---

## 🛡️ Post-Deployment Security

### Security Hardening

```bash
# Update system
apt update && apt upgrade -y

# Enable firewall
ufw enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Disable root login
nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no

systemctl restart sshd
```

- [ ] System packages updated
- [ ] UFW firewall enabled
- [ ] SSH hardened
- [ ] Only public key authentication allowed

### Monitoring & Alerts

- [ ] Set up monitoring (Uptime Kuma, StatusCake, or similar)
- [ ] Configure email notifications
- [ ] Monitor disk space: `df -h`
- [ ] Monitor memory: `free -h`
- [ ] Monitor logs: `docker-compose logs -f`

---

## 📊 Maintenance Schedule

### Daily
- [ ] Check application is accessible
- [ ] Monitor logs for errors: `docker-compose logs --tail=100`

### Weekly
- [ ] Check disk space: `df -h`
- [ ] Review error logs
- [ ] Test backup restoration

### Monthly
- [ ] Database backup verification
- [ ] Security updates
- [ ] SSL certificate renewal test

### Quarterly
- [ ] Security audit
- [ ] Performance review
- [ ] Dependencies update

---

## 🔄 Backup & Recovery

### Automated Backup Setup

```bash
nano /usr/local/bin/backup-hermes.sh
```

Add the backup script (see DEPLOY_DOCKER_HOSTINGER.md)

```bash
chmod +x /usr/local/bin/backup-hermes.sh

crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-hermes.sh
```

- [ ] Backup script created
- [ ] Backup scheduled in crontab
- [ ] First backup completed

### Manual Backup

```bash
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U hermes_user -d hermes_db | gzip > backups/hermes_backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

- [ ] Manual backup executed and verified

---

## 📞 Common Commands

### View Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### Restart Services
```bash
# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart and rebuild
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Database Operations
```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U hermes_user -d hermes_db

# Backup
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U hermes_user -d hermes_db > backup.sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U hermes_user -d hermes_db < backup.sql
```

### Container Management
```bash
# See all running containers
docker ps

# Execute command in container
docker-compose -f docker-compose.prod.yml exec backend bash

# View container stats
docker stats

# Clean up unused images
docker image prune -a -f
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | `docker-compose ps` - check if services running |
| Database error | Check DATABASE_URL in .env.production.local |
| SSL certificate invalid | Verify certificates in ssl/ directory |
| 502 Bad Gateway | Check backend logs: `docker-compose logs backend` |
| Out of memory | Check: `free -h`, increase VPS RAM or add swap |
| Can't reach domain | Verify DNS: `nslookup your-domain.com` |
| Container won't start | Check logs: `docker logs container_name` |

---

## 📚 Documentation Files

- **DEPLOY_DOCKER_HOSTINGER.md** - Full Docker deployment guide
- **DEPLOY_HOSTINGER.md** - Traditional deployment guide (without Docker)
- **docker-compose.prod.yml** - Production Docker Compose configuration
- **nginx.conf** - Nginx reverse proxy configuration
- **.env.production** - Environment variables template
- **deploy-hostinger.sh** - Automated deployment script

---

## ✅ Final Verification

- [ ] Application accessible at https://your-domain.com/app.html
- [ ] SSL certificate valid and not self-signed (except dev)
- [ ] API endpoints responding
- [ ] Database connected and working
- [ ] Telegram bot responding
- [ ] All containers healthy: `docker-compose ps`
- [ ] Backup schedule set
- [ ] Monitoring configured
- [ ] Security hardened

---

## 🎉 Deployment Complete!

Your Hermes AI Skill Hub is now live on Hostinger VPS with Docker!

**Keep monitoring:**
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

**Need help?**
- Check DEPLOY_DOCKER_HOSTINGER.md for detailed guide
- Review docker-compose logs: `docker-compose logs service_name`
- Hostinger Support: https://support.hostinger.com

---

**Last Updated:** 2026-06-09
