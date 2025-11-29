# 🚀 News Automation System - Deployment Guide

## Overview
This guide covers the deployment, backup, and rollback procedures for the News Automation Frontend.

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Deployment](#deployment)
3. [Backup Procedures](#backup-procedures)
4. [Rollback Procedures](#rollback-procedures)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Disk Space**: At least 5GB free space
- **Memory**: At least 4GB RAM
- **CPU**: 2+ cores recommended

### Network Requirements
- Port 3002 available (Express API proxy)
- Port 3003 available (Nginx static files - optional)
- Access to Docker internal network

### Verify Prerequisites
```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Check available disk space
df -h

# Check if ports are available
lsof -i :3002
lsof -i :3003
```

---

## 🚀 Deployment

### Method 1: Automated Deployment (Recommended)

The automated deployment script handles:
- ✅ Pre-deployment checks
- ✅ Automatic backup creation
- ✅ Image building
- ✅ Container deployment
- ✅ Health checks
- ✅ Rollback on failure

**Run the deployment:**
```bash
./scripts/deploy-frontend.sh
```

**What it does:**
1. Checks Docker and Docker Compose availability
2. Creates a backup of the current deployment
3. Builds the new Docker image
4. Stops the current container
5. Starts the new container
6. Runs health checks (30 attempts, 2s interval)
7. Cleans up old images
8. Shows deployment status

**Expected Output:**
```
==========================================
Starting Frontend Deployment
==========================================
✅ Docker is running
✅ Docker Compose is available
📦 Creating backup: frontend_backup_20251129_210000
✅ Backup created
🔨 Building Docker image...
✅ Image built successfully
🛑 Stopping container...
✅ Container stopped
🚀 Starting container...
✅ Container started
🏥 Waiting for service to be healthy...
✅ Health check passed
==========================================
Deployment Successful
==========================================
✅ Frontend deployed successfully!
🌐 Frontend is available at: http://localhost:3002
```

### Method 2: Manual Deployment

**Step 1: Build the image**
```bash
docker-compose build news-automation-frontend
```

**Step 2: Start the container**
```bash
docker-compose up -d news-automation-frontend
```

**Step 3: Check health**
```bash
curl http://localhost:3002/health
```

**Step 4: View logs**
```bash
docker logs -f news-automation-frontend
```

### Method 3: Production Deployment with Nginx

For production with Nginx serving static files:

**Step 1: Use production Dockerfile**
```bash
# Edit docker-compose.yml to use Dockerfile.production
# Change: dockerfile: Dockerfile
# To: dockerfile: Dockerfile.production
```

**Step 2: Deploy**
```bash
docker-compose up -d --build news-automation-frontend
```

**Step 3: Access**
- Frontend UI: http://localhost:3003 (Nginx)
- API Proxy: http://localhost:3002 (Express)

---

## 💾 Backup Procedures

### Automated Backup

**Create a backup:**
```bash
./scripts/backup-frontend.sh create
```

**What it backs up:**
- Container export (TAR file)
- Container logs
- Container configuration (inspect JSON)
- Image information
- Environment variables
- Backup metadata

**Backup location:**
```
backups/
├── frontend_backup_20251129_210000/
│   ├── container.tar
│   ├── container.log
│   ├── container-inspect.json
│   ├── image-inspect.json
│   ├── image-id.txt
│   ├── environment.txt
│   └── metadata.json
└── latest_backup.txt
```

**List all backups:**
```bash
./scripts/backup-frontend.sh list
```

**Cleanup old backups:**
```bash
./scripts/backup-frontend.sh cleanup
```

**Backup retention:**
- Keeps 10 most recent backups by default
- Automatically removes older backups
- Configurable in `scripts/backup-frontend.sh` (MAX_BACKUPS variable)

### Manual Backup

**Export container:**
```bash
docker export news-automation-frontend > frontend-backup.tar
```

**Save logs:**
```bash
docker logs news-automation-frontend > frontend-logs.txt
```

**Save configuration:**
```bash
docker inspect news-automation-frontend > frontend-config.json
```

---

## ⏮️ Rollback Procedures

### Automated Rollback

**Rollback to latest backup:**
```bash
./scripts/rollback-frontend.sh
```

**What it does:**
1. Lists available backups
2. Confirms rollback action
3. Stops current container
4. Removes current container
5. Rebuilds from source
6. Starts container
7. Runs health checks

**Expected Output:**
```
==========================================
Starting Frontend Rollback
==========================================
📋 Rolling back to: frontend_backup_20251129_210000
Are you sure you want to rollback? (yes/no): yes
🛑 Stopping container...
✅ Container stopped
🗑️  Removing container...
✅ Container removed
🔨 Rebuilding frontend from source...
✅ Build completed
🚀 Starting container from backup...
✅ Container started
🏥 Waiting for service to be healthy...
✅ Health check passed
==========================================
Rollback Successful
==========================================
✅ Frontend rolled back successfully!
```

### Manual Rollback

**Step 1: Stop current container**
```bash
docker-compose stop news-automation-frontend
```

**Step 2: Remove current container**
```bash
docker-compose rm -f news-automation-frontend
```

**Step 3: Rebuild from source**
```bash
docker-compose build news-automation-frontend
```

**Step 4: Start container**
```bash
docker-compose up -d news-automation-frontend
```

---

## 📊 Monitoring

### Container Status

**Check if container is running:**
```bash
docker ps --filter "name=news-automation-frontend"
```

**Check container health:**
```bash
docker inspect --format='{{.State.Health.Status}}' news-automation-frontend
```

**View container stats:**
```bash
docker stats news-automation-frontend
```

### Logs

**View real-time logs:**
```bash
docker logs -f news-automation-frontend
```

**View last 100 lines:**
```bash
docker logs --tail 100 news-automation-frontend
```

**View logs with timestamps:**
```bash
docker logs -t news-automation-frontend
```

**Search logs:**
```bash
docker logs news-automation-frontend 2>&1 | grep "ERROR"
```

### Health Checks

**Manual health check:**
```bash
curl http://localhost:3002/health
```

**Expected response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-29T21:00:00.000Z"
}
```

**Check health check history:**
```bash
docker inspect --format='{{json .State.Health}}' news-automation-frontend | jq
```

### Performance Monitoring

**Resource usage:**
```bash
docker stats news-automation-frontend --no-stream
```

**Disk usage:**
```bash
docker system df
```

**Network connections:**
```bash
docker exec news-automation-frontend netstat -an | grep ESTABLISHED
```

---

## 🔧 Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs news-automation-frontend
```

**Common issues:**
1. **Port already in use**
   ```bash
   # Find process using port 3002
   lsof -i :3002
   # Kill the process
   kill -9 <PID>
   ```

2. **Missing dependencies**
   ```bash
   # Rebuild with no cache
   docker-compose build --no-cache news-automation-frontend
   ```

3. **Network issues**
   ```bash
   # Recreate network
   docker network rm ichat-network
   docker-compose up -d
   ```

### Health Check Failing

**Check if service is responding:**
```bash
docker exec news-automation-frontend curl http://localhost:3002/health
```

**Check if Express server is running:**
```bash
docker exec news-automation-frontend ps aux | grep node
```

**Restart container:**
```bash
docker-compose restart news-automation-frontend
```

### High Memory Usage

**Check memory stats:**
```bash
docker stats news-automation-frontend --no-stream
```

**Restart container to free memory:**
```bash
docker-compose restart news-automation-frontend
```

**Increase memory limit in docker-compose.yml:**
```yaml
deploy:
  resources:
    limits:
      memory: 2G
```

### Slow Performance

**Check resource usage:**
```bash
docker stats news-automation-frontend
```

**Check network latency:**
```bash
docker exec news-automation-frontend ping ichat-api-server
```

**Optimize build:**
```bash
# Use production Dockerfile with Nginx
# Edit docker-compose.yml: dockerfile: Dockerfile.production
docker-compose up -d --build news-automation-frontend
```

### Cannot Access Frontend

**Check if container is running:**
```bash
docker ps | grep news-automation-frontend
```

**Check port mapping:**
```bash
docker port news-automation-frontend
```

**Check firewall:**
```bash
# macOS
sudo pfctl -sr | grep 3002

# Linux
sudo iptables -L | grep 3002
```

**Test from inside container:**
```bash
docker exec news-automation-frontend curl http://localhost:3002
```

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] Verify Docker and Docker Compose are installed
- [ ] Check available disk space (>5GB)
- [ ] Verify ports 3002 and 3003 are available
- [ ] Review environment variables in docker-compose.yml
- [ ] Create backup of current deployment

### Deployment
- [ ] Run deployment script or manual deployment
- [ ] Monitor deployment logs
- [ ] Wait for health checks to pass
- [ ] Verify container is running

### Post-Deployment
- [ ] Test frontend UI (http://localhost:3002)
- [ ] Test API endpoints
- [ ] Check logs for errors
- [ ] Monitor resource usage
- [ ] Update documentation if needed

### Rollback (if needed)
- [ ] Run rollback script
- [ ] Verify rollback completed successfully
- [ ] Test frontend functionality
- [ ] Investigate deployment failure
- [ ] Fix issues before next deployment

---

## 🎯 Best Practices

1. **Always create backups before deployment**
2. **Test in development environment first**
3. **Monitor logs during deployment**
4. **Keep at least 10 recent backups**
5. **Document any configuration changes**
6. **Use automated scripts for consistency**
7. **Run health checks after deployment**
8. **Monitor resource usage regularly**
9. **Keep deployment logs for troubleshooting**
10. **Have a rollback plan ready**

---

## 📞 Support

For issues or questions:
1. Check the logs: `docker logs news-automation-frontend`
2. Review this deployment guide
3. Check the troubleshooting section
4. Contact the development team

---

**Last Updated**: 2025-11-29
**Version**: 1.0.0

