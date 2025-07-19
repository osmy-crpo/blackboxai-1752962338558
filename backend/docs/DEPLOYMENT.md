# Warehouse Management System - Production Deployment Guide

## Overview

This guide provides instructions to deploy the Warehouse Management System backend and frontend in production using Docker and Docker Compose.

---

## Prerequisites

- Docker and Docker Compose installed on the server
- Domain name configured with DNS pointing to your server IP
- SSL certificate (recommended: Let's Encrypt)
- SMTP credentials for email notifications

---

## Step 1: Clone the Repository

```bash
git clone https://your-repo-url.git
cd warehouse-management-system
```

---

## Step 2: Configure Environment Variables

Copy the production environment template and update values:

```bash
cp backend/.env.production backend/.env
nano backend/.env
```

- Set `SECRET_KEY` to a strong, unique value
- Update `ALLOWED_HOSTS` with your domain and IP addresses
- Configure SMTP settings for email notifications
- Adjust other settings as needed

---

## Step 3: Build and Start Containers

```bash
docker-compose up -d --build
```

This will build and start the backend, frontend, PostgreSQL, and Redis containers.

---

## Step 4: Verify Services

- Backend API: http://yourdomain.com:8001/docs
- Frontend App: http://yourdomain.com:8000

Check logs for errors:

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## Step 5: Configure Reverse Proxy and HTTPS

Use Nginx or Caddy to proxy requests and enable HTTPS.

Example Nginx config:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Use Certbot to obtain SSL certificates:

```bash
sudo certbot --nginx -d yourdomain.com
```

---

## Step 6: Setup Automated Backups

Configure a cron job or systemd timer to run database backups:

Example backup script:

```bash
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR=/path/to/backups
mkdir -p $BACKUP_DIR
docker exec warehouse-db pg_dump -U warehouse_user warehouse_db > $BACKUP_DIR/warehouse_db_$TIMESTAMP.sql
find $BACKUP_DIR -type f -mtime +30 -delete
```

Schedule in crontab:

```bash
0 2 * * * /path/to/backup_script.sh
```

---

## Step 7: Enable Monitoring and Logging

- Use Docker logging drivers or external logging services
- Monitor container health and resource usage
- Set up alerts for failures or performance issues

---

## Additional Notes

- Always keep your `SECRET_KEY` secure and never commit it to version control
- Regularly update dependencies and apply security patches
- Test backups and recovery procedures periodically
- Consider setting up a staging environment for testing before production deployment

---

**For further assistance, consult the project documentation or contact the development team.**
