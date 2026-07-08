# 🎬 BARKSDALE VIDEO STUDIO

AI-powered video storyboard generator with 500+ director style profiles. Transform scripts into cinematic masterpieces.

![Version](https://img.shields.io/badge/version-2.0.0-orange)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![React](https://img.shields.io/badge/react-18-blue)

## ✨ Features

- **🎬 Director Library**: 500+ iconic directors with detailed cinematic profiles
- **📝 Script Analysis**: AI-powered scene breakdown and storyboard generation
- **🎨 Style Transfer**: Apply director-specific color palettes, camera styles, and moods
- **🎥 Video Generation**: Async video generation using Stable Video Diffusion
- **🔐 Authentication**: JWT-based auth with rate limiting
- **📱 Responsive**: Mobile-first design with dark/light mode

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                        │
│                     GitHub Pages / Vercel                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│                       Render / Railway                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │   Auth API   │  │ Directors API│  │  Generation API       │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
│           │               │                    │               │
│           └───────────────┼────────────────────┘               │
│                           ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              CELERY WORKER (Async Jobs)                    │ │
│  │         Redis Queue │ Video Generation                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────┬─────────────────────┬──────────────────────────────┘
            │                     │
            ▼                     ▼
┌──────────────────┐    ┌──────────────────┐
│   PostgreSQL      │    │     Redis         │
│   (Directors,     │    │   (Job Queue,     │
│    Users, Jobs)    │    │    Cache)         │
└──────────────────┘    └──────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│  TMDB API │ OpenAI │ Replicate │ AWS S3 / Cloudinary            │
└──────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/barksdale410/barksdale-video-studio.git
cd barksdale-video-studio

# Copy environment variables
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys

# Start all services
docker-compose up -d

# The app will be available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8001
# - API Docs: http://localhost:8001/docs
```

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
alembic upgrade head
python scripts/seed_directors.py --featured
uvicorn app.main:app --reload --port 8001
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentation

- [Deployment Guide](./deployment.md) - Deploy to Render, GitHub Pages, etc.
- [API Documentation](./API.md) - Complete API reference
- [Contributing Guide](./CONTRIBUTING.md) - How to contribute
- [Improvements](./IMPROVEMENTS.md) - Future upgrade plans

## 🔌 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login |
| `/api/v1/auth/me` | GET | Get current user |

### Directors
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/directors` | GET | List directors (with filters) |
| `/api/v1/directors/{id}` | GET | Get director profile |
| `/api/v1/directors/random` | GET | Random director |
| `/api/v1/directors/letters` | GET | Available letters |
| `/api/v1/directors/favorites` | POST | Add to favorites |

### Script Analysis
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analyze` | POST | Analyze script |

### Video Generation
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/generate` | POST | Start generation |
| `/api/v1/jobs/{id}/status` | GET | Check status |
| `/api/v1/jobs/{id}` | GET | Get job details |

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM
- PostgreSQL - Primary database
- Redis + Celery - Async task queue
- JWT Auth - Secure authentication

**Frontend:**
- React 18 - UI framework
- Tailwind CSS - Styling
- Framer Motion - Animations
- Vite - Build tool

**Infrastructure:**
- Docker - Containerization
- Render - Backend hosting
- GitHub Pages - Frontend hosting
- TMDB API - Director data
- OpenAI - Style profiling
- Replicate - Video generation

## 📦 Project Structure

```
barksdale-video-studio/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, security, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routes/         # API routes
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── tasks/          # Celery tasks
│   │   └── main.py         # FastAPI app
│   ├── scripts/
│   │   └── seed_directors.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── contexts/
│   │   ├── hooks/
│   │   └── utils/
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .github/workflows/
├── deployment.md
├── CONTRIBUTING.md
├── IMPROVEMENTS.md
└── README.md
```

## 🔒 Environment Variables

See [`.env.example`](backend/.env.example) for all required variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# Auth
SECRET_KEY=your-secret-key

# External APIs
TMDB_API_KEY=your-tmdb-key
OPENAI_API_KEY=your-openai-key
REPLICATE_API_TOKEN=your-replicate-token
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [TMDB](https://www.themoviedb.org/) for director and film data
- [OpenAI](https://openai.com/) for GPT-4o mini
- [Replicate](https://replicate.com/) for video generation
- All the amazing open-source libraries used in this project

---

Built with ❤️ by the Barksdale Video Studio Team