# Deployment Guide

This guide covers deploying the Barksdale Video Studio to production.

## 🐳 Option 1: Docker (Recommended for Development)

```bash
# Clone and setup
git clone https://github.com/barksdale410/barksdale-video-studio.git
cd barksdale-video-studio

# Copy environment file
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend alembic upgrade head

# Seed directors
docker-compose exec backend python scripts/seed_directors.py --featured

# View logs
docker-compose logs -f
```

---

## ☁️ Option 2: Render Deployment

### Backend (Web Service)

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create PostgreSQL Database**
   - New → PostgreSQL
   - Name: `barksdale-db`
   - Select region closest to you
   - Copy the Internal Database URL

3. **Create Redis Instance**
   - New → Redis
   - Name: `barksdale-redis`
   - Copy the Redis URL

4. **Deploy Backend**
   - New → Web Service
   - Connect GitHub repo
   - Configure:
     ```
     Name: barksdale-api
     Region: Choose closest
     Branch: main
     Root Directory: (leave empty)
     Runtime: Python 3
     Build Command: pip install -r backend/requirements.txt
     Start Command: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8001
     ```
   - Add Environment Variables:
     ```
     DATABASE_URL: (your PostgreSQL URL)
     REDIS_URL: (your Redis URL)
     SECRET_KEY: (generate a secure random string)
     DEBUG: false
     ```

5. **Seed Database (via SSH)**
   - Enable SSH for the web service
   - Connect: `renderctl service ssh --service=barksdale-api`
   - Run:
     ```bash
     cd /app/backend
     pip install -r requirements.txt
     python scripts/seed_directors.py --featured
     ```

### Worker (Celery)

1. **Deploy Celery Worker**
   - New → Background Worker
   - Same repo settings
   - Configure:
     ```
     Name: barksdale-worker
     Start Command: cd backend && celery -A app.tasks.video_tasks worker --loglevel=info
     ```
   - Add same Environment Variables as backend

### Frontend (GitHub Pages)

1. **Update API URL**
   - Edit `frontend/src/utils/api.js`
   - Change `API_BASE_URL` to your Render backend URL

2. **Build Frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. **Deploy**
   - Enable GitHub Pages in repository Settings
   - Source: Deploy from branch
   - Branch: `gh-pages` / `(root)`

---

## 🔧 Manual Deployment

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Backend Setup

```bash
# Clone repo
git clone https://github.com/barksdale410/barksdale-video-studio.git
cd barksdale-video-studio/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
alembic upgrade head

# Seed directors
python scripts/seed_directors.py --featured

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx
# Copy nginx.conf to /etc/nginx/sites-available/
# Enable site and restart nginx
```

---

## 🔐 Environment Variables

### Required
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing key (generate securely) |

### Optional
| Variable | Description |
|----------|-------------|
| `TMDB_API_KEY` | TMDB API key for director data |
| `OPENAI_API_KEY` | OpenAI API for style generation |
| `REPLICATE_API_TOKEN` | Replicate for video generation |
| `DEBUG` | Enable debug mode (default: false) |

---

## ✅ Post-Deployment Checklist

- [ ] Backend health check returns 200
- [ ] API docs accessible at `/docs`
- [ ] Database migrations applied
- [ ] Directors seeded
- [ ] Frontend connects to backend
- [ ] Authentication works
- [ ] Rate limiting configured
- [ ] Monitoring/alerting set up

---

## 🆘 Troubleshooting

### Backend Issues

**Database connection failed:**
- Check `DATABASE_URL` format
- Verify PostgreSQL is accessible
- Check connection pooling settings

**Redis connection failed:**
- Verify Redis URL
- Check if Redis is running
- Verify network access

**CORS errors:**
- Update `CORS_ORIGINS` in config
- Check frontend API URL configuration

### Frontend Issues

**API not responding:**
- Verify backend is running
- Check API URL in frontend config
- Verify CORS settings

**Build failures:**
- Clear node_modules: `rm -rf node_modules package-lock.json`
- Reinstall: `npm install`

---

## 📊 Monitoring

### Health Check
```bash
curl https://your-api.onrender.com/api/v1/health
```

### View Logs
In Render dashboard → your service → Logs tab

### Metrics
Consider adding:
- Sentry for error tracking
- Datadog for APM
- Prometheus for metrics
