# 🚀 Deployment Guide - Hostinger VPS

Hermes AI Skill Hub on Hostinger VPS with Managed Database

---

## 📋 Checklist ก่อน Deploy

- [ ] ซื้อ VPS บน Hostinger
- [ ] ซื้อ/ตั้งค่า Domain
- [ ] สร้าง Hostinger Managed Database
- [ ] เตรียม SSH credentials
- [ ] เตรียม API Keys (OpenAI, Anthropic, Telegram)

---

## 🔧 ขั้นตอนการ Deploy

### **Phase 1: Server Setup (บน Hostinger VPS)**

#### 1.1 SSH เข้าเซิร์ฟเวอร์
```bash
ssh root@your_vps_ip
# หรือ
ssh your_username@your_vps_ip
```

#### 1.2 Update System
```bash
apt update && apt upgrade -y
```

#### 1.3 ติดตั้ง Dependencies
```bash
# Python, Git, Build tools
apt install -y python3.10 python3.10-venv python3-pip git curl wget

# Node.js (optional, สำหรับ frontend build)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs

# Supervisor (สำหรับ manage processes)
apt install -y supervisor

# Nginx (reverse proxy)
apt install -y nginx
```

#### 1.4 ตั้งค่า Firewall
```bash
# Enable UFW
ufw enable

# Allow SSH, HTTP, HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Check status
ufw status
```

---

### **Phase 2: Application Setup**

#### 2.1 Clone Repository
```bash
cd /var/www
git clone https://github.com/narisarapaewpairee/hermes-ai-skill-hub.git
cd hermes-ai-skill-hub
```

#### 2.2 สร้าง Virtual Environment
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### 2.3 ตั้งค่า Environment Variables
```bash
nano .env
```

ใส่ค่าต่อไปนี้:
```env
# Database - จาก Hostinger Managed Database
DATABASE_URL=postgresql://your_db_user:your_db_password@your_managed_db_host:5432/your_db_name

# Backend
BACKEND_URL=https://your_domain.com
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id

# OpenAI & Anthropic APIs
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Environment
ENVIRONMENT=production
DEBUG=False

# Security
SECRET_KEY=your_secure_random_secret_key_here
```

**⚠️ สำคัญ:** ไม่ควร commit `.env` ลง Git

---

### **Phase 3: Database Setup**

#### 3.1 ตั้งค่า Hostinger Managed Database

ไปที่ Hostinger Dashboard → Managed Database
- สร้าง PostgreSQL database
- จดบันทึก: hostname, username, password, database name
- เปิด firewall access จาก VPS IP ของคุณ

#### 3.2 Initialize Database Schema
```bash
# Activate venv
source .venv/bin/activate

# Run database migrations
cd backend
python3 -c "from models import Base, engine; Base.metadata.create_all(bind=engine)"

# Verify connection
python3 -c "from sqlalchemy import create_engine; import os; e = create_engine(os.getenv('DATABASE_URL')); print(e.execute('SELECT 1').fetchone())"
```

---

### **Phase 4: Supervisor Configuration** (Auto-restart processes)

#### 4.1 สร้าง Supervisor Config สำหรับ Backend
```bash
sudo nano /etc/supervisor/conf.d/hermes-backend.conf
```

ใส่:
```ini
[program:hermes-backend]
directory=/var/www/hermes-ai-skill-hub
command=/var/www/hermes-ai-skill-hub/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/hermes-backend.err.log
stdout_logfile=/var/log/hermes-backend.out.log
environment=PATH="/var/www/hermes-ai-skill-hub/.venv/bin",DATABASE_URL="postgresql://...",TELEGRAM_BOT_TOKEN="..."
```

#### 4.2 Update Supervisor
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start hermes-backend
sudo supervisorctl status
```

---

### **Phase 5: Nginx Configuration** (Reverse Proxy)

#### 5.1 สร้าง Nginx Config
```bash
sudo nano /etc/nginx/sites-available/hermes
```

ใส่:
```nginx
upstream hermes_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your_domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your_domain.com;

    # SSL Certificates (ใช้ Let's Encrypt ผ่าน Certbot)
    ssl_certificate /etc/letsencrypt/live/your_domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your_domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/json;

    # Frontend (Static files)
    location / {
        root /var/www/hermes-ai-skill-hub;
        try_files $uri /app.html;
    }

    # Backend API
    location /api {
        proxy_pass http://hermes_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

#### 5.2 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/hermes /etc/nginx/sites-enabled/hermes
sudo nginx -t  # Test config
sudo systemctl restart nginx
```

---

### **Phase 6: SSL Certificate** (Let's Encrypt)

#### 6.1 ติดตั้ง Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

#### 6.2 สร้าง Certificate
```bash
sudo certbot certonly --nginx -d your_domain.com -d www.your_domain.com
```

---

### **Phase 7: Verify & Test**

#### 7.1 ตรวจสอบ Services
```bash
# Backend
curl http://127.0.0.1:8000/docs

# Database connection
psql -h your_managed_db_host -U your_db_user -d your_db_name -c "SELECT 1"

# Supervisor
sudo supervisorctl status hermes-backend

# Nginx
sudo systemctl status nginx
```

#### 7.2 เข้าเว็บผ่าน Browser
```
https://your_domain.com/app.html
```

---

### **Phase 8: Monitoring & Maintenance**

#### 8.1 Check Logs
```bash
# Backend logs
sudo tail -f /var/log/hermes-backend.out.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
journalctl -u nginx -f
```

#### 8.2 Auto-renew SSL
```bash
# Test renewal
sudo certbot renew --dry-run

# Enable auto-renew
sudo systemctl enable certbot.timer
```

#### 8.3 Database Backups
```bash
# Manual backup
pg_dump -h your_db_host -U your_db_user -d your_db_name > hermes_backup_$(date +%Y%m%d).sql

# Scheduled backup (cron)
# Edit: crontab -e
# Add: 0 2 * * * pg_dump -h your_db_host -U your_db_user -d your_db_name > /backups/hermes_$(date +\%Y\%m\%d).sql
```

---

## 🔐 Security Best Practices

1. **SSH Keys** - ใช้ SSH key แทน password
2. **.env File** - ไม่ให้ commit ลง Git
3. **Firewall** - เปิดเฉพาะ port ที่ต้องการ
4. **SSL/TLS** - ใช้ HTTPS เสมอ
5. **Database** - ใช้ strong password, backup regularly
6. **Secrets** - เก็บ API keys ใน environment variables

---

## 🐛 Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|---------|
| Backend ไม่ connect Database | ตรวจสอบ DATABASE_URL และ Firewall rules |
| Nginx 502 Bad Gateway | ตรวจสอบ `sudo supervisorctl status` |
| SSL Certificate expired | `sudo certbot renew` |
| Out of memory | เพิ่ม swap: `fallocate -l 2G /swapfile` |

---

## 📞 Support

- Hostinger Support: https://www.hostinger.com/support
- FastAPI Docs: https://fastapi.tiangolo.com/
- PostgreSQL Docs: https://www.postgresql.org/docs/

---

**Last Updated:** 2026-06-09
