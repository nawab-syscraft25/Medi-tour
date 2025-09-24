# 🚀 Manual Deployment Guide for Medi-Tour API

## 📋 Prerequisites

- Python 3.11+
- Git
- A server (VPS, cloud instance, or local machine)
- Domain name (optional)

## 🖥️ Server Setup (Ubuntu/Debian)

### Step 1: Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Required Packages
```bash
# Install Python and essential tools
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install -y git curl nginx certbot python3-certbot-nginx
sudo apt install -y build-essential libssl-dev libffi-dev

# Install PostgreSQL (recommended for production)
sudo apt install -y postgresql postgresql-contrib
```

### Step 3: Create Application User
```bash
# Create a dedicated user for the app
sudo adduser --system --group --home /opt/meditour meditour
sudo mkdir -p /opt/meditour
sudo chown meditour:meditour /opt/meditour
```

## 📁 Application Deployment

### Step 4: Clone and Setup Application
```bash
# Switch to application user
sudo su - meditour

# Clone your repository
cd /opt/meditour
git clone https://github.com/your-username/medi-tour.git app
cd app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Environment Configuration
```bash
# Create production environment file
nano .env.production
```

Add this content to `.env.production`:
```env
# Database
DATABASE_URL=postgresql://meditour:your_password@localhost:5432/meditour

# Security
SECRET_KEY=your-super-secret-key-min-32-characters-long-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Environment
DEBUG=false
ENVIRONMENT=production

# Upload settings
MAX_UPLOAD_SIZE=10485760
ALLOWED_IMAGE_EXTENSIONS=jpg,jpeg,png,webp
ALLOWED_DOC_EXTENSIONS=pdf,doc,docx
MAX_IMAGES_PER_OWNER=5

# AWS S3 (optional, for file storage)
# AWS_ACCESS_KEY_ID=your-aws-key
# AWS_SECRET_ACCESS_KEY=your-aws-secret
# S3_BUCKET_NAME=your-bucket-name
# S3_REGION=us-east-1
```

### Step 6: Database Setup
```bash
# Exit from meditour user
exit

# Configure PostgreSQL
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE meditour;
CREATE USER meditour WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE meditour TO meditour;
\q

# Switch back to meditour user and run migrations
sudo su - meditour
cd /opt/meditour/app
source venv/bin/activate
export $(cat .env.production | xargs)
alembic upgrade head
```

### Step 7: Create Media Directory
```bash
# Still as meditour user
mkdir -p /opt/meditour/app/media/uploads
mkdir -p /opt/meditour/app/media/hospital
mkdir -p /opt/meditour/app/media/doctor
mkdir -p /opt/meditour/app/media/treatment
```

## 🔧 Process Management with Systemd

### Step 8: Create Systemd Service
```bash
# Exit from meditour user
exit

# Create systemd service file
sudo nano /etc/systemd/system/meditour.service
```

Add this content:
```ini
[Unit]
Description=Medi-Tour FastAPI application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=meditour
Group=meditour
WorkingDirectory=/opt/meditour/app
Environment=PATH=/opt/meditour/app/venv/bin
EnvironmentFile=/opt/meditour/app/.env.production
ExecStart=/opt/meditour/app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Step 9: Start and Enable Service
```bash
# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable meditour
sudo systemctl start meditour

# Check status
sudo systemctl status meditour

# View logs
sudo journalctl -u meditour -f
```

## 🌐 Nginx Reverse Proxy (Optional)

### Step 10: Configure Nginx
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/meditour
```

Add this content:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;  # Replace with your domain

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Serve media files directly
    location /media/ {
        alias /opt/meditour/app/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Step 11: Enable Nginx Site
```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/meditour /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

## 🔒 SSL Certificate (Optional)

### Step 12: Get SSL Certificate
```bash
# Get Let's Encrypt certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (already set up by certbot)
sudo systemctl status certbot.timer
```

## 🚀 Direct Deployment (Without Nginx)

If you want to run directly on port 8000 without Nginx:

### Option A: Run on Port 8000
```bash
# Modify systemd service to bind to 0.0.0.0:8000
sudo nano /etc/systemd/system/meditour.service

# Change ExecStart line to:
ExecStart=/opt/meditour/app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart meditour
```

### Option B: Run on Port 80 (Requires sudo)
```bash
# Allow binding to port 80
sudo setcap 'cap_net_bind_service=+ep' /opt/meditour/app/venv/bin/python

# Modify service to use port 80
ExecStart=/opt/meditour/app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 80 --workers 4
```

## 🔧 Management Commands

### Check Application Status
```bash
# Service status
sudo systemctl status meditour

# View logs
sudo journalctl -u meditour -f

# Restart application
sudo systemctl restart meditour
```

### Update Application
```bash
# Switch to meditour user
sudo su - meditour
cd /opt/meditour/app

# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
export $(cat .env.production | xargs)
alembic upgrade head

# Exit and restart service
exit
sudo systemctl restart meditour
```

### Database Management
```bash
# Connect to database
sudo -u postgres psql -d meditour

# Backup database
sudo -u postgres pg_dump meditour > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
sudo -u postgres psql meditour < backup_file.sql
```

## 🔥 Firewall Configuration

### Configure UFW (Ubuntu Firewall)
```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS (if using Nginx)
sudo ufw allow 'Nginx Full'

# OR allow port 8000 directly (if not using Nginx)
sudo ufw allow 8000

# Check status
sudo ufw status
```

## 📊 Monitoring

### Check if API is running
```bash
# Test locally
curl http://localhost:8000/health

# Test externally (replace with your IP/domain)
curl http://your-server-ip:8000/health
```

### Performance Monitoring
```bash
# Monitor processes
htop

# Check disk usage
df -h

# Check memory
free -h

# Monitor logs
tail -f /var/log/nginx/access.log  # If using Nginx
sudo journalctl -u meditour -f     # Application logs
```

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**
```bash
# Check logs
sudo journalctl -u meditour --no-pager

# Check permissions
sudo chown -R meditour:meditour /opt/meditour
```

2. **Database connection failed**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
sudo -u meditour psql -h localhost -U meditour -d meditour
```

3. **Permission denied for media files**
```bash
# Fix permissions
sudo chown -R meditour:meditour /opt/meditour/app/media
sudo chmod -R 755 /opt/meditour/app/media
```

4. **Port already in use**
```bash
# Check what's using the port
sudo netstat -tlnp | grep :8000

# Kill process if needed
sudo kill -9 <process_id>
```

## 🎯 Final Access Points

After successful deployment:

- **API**: `http://your-server-ip:8000` or `https://your-domain.com`
- **Documentation**: `http://your-server-ip:8000/docs`
- **Health Check**: `http://your-server-ip:8000/health`
- **Admin**: Use your created admin credentials

## 📝 Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database password
- [ ] Configure firewall (UFW)
- [ ] Set up SSL certificate
- [ ] Regular security updates
- [ ] Monitor logs regularly
- [ ] Backup database regularly

Your API is now manually deployed and ready for production use! 🎉