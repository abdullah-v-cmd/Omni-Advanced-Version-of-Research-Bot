# OmniSynth Deployment Guide

## Production Deployment

### 1. Server Requirements
- CPU: 4+ cores (8 recommended for AI workloads)
- RAM: 8GB minimum (16GB recommended)
- Storage: 50GB+ SSD
- OS: Ubuntu 22.04 LTS

### 2. Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo apt-get install -y docker-compose-plugin
```

### 3. Clone & Configure
```bash
git clone https://github.com/YOUR_USERNAME/test.git omnisynth
cd omnisynth
cp backend/.env.example backend/.env
# Edit backend/.env - set GROQ_API_KEY, SECRET_KEY, etc.
```

### 4. Launch
```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

### 5. SSL with Let's Encrypt (optional)
```bash
sudo apt install certbot
certbot certonly --standalone -d yourdomain.com
# Update nginx.conf to use SSL
```

## Scaling
- Backend: Increase uvicorn workers in Dockerfile CMD
- Celery: Add more worker replicas in docker-compose.yml
- Database: Use managed PostgreSQL (RDS, Cloud SQL, Supabase)
- Redis: Use managed Redis (ElastiCache, Upstash)
