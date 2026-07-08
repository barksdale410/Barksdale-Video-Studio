# Deployment Guide

## Backend (Render)

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up / Log in with GitHub

### Step 2: Deploy the Backend
1. Click "New +" → "Web Service"
2. Connect your GitHub account
3. Select the `barksdale410/barksdale-video-studio` repository
4. Configure the service:
   - **Name**: `barksdale-video-studio-api`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn server:app --host 0.0.0.0 --port 8001`
   - **Plan**: Free tier is sufficient for testing

5. Click "Create Web Service"
6. Wait for deployment to complete
7. Note your backend URL (e.g., `https://barksdale-video-studio-api.onrender.com`)

### Step 3: Verify Backend
Visit `https://barksdale-video-studio-api.onrender.com/api/health` - you should see:
```json
{"status":"healthy","service":"Barksdale Video Studio API"}
```

---

## Frontend (GitHub Pages)

### Step 1: Enable GitHub Pages
1. Go to the repository: `https://github.com/barksdale410/barksdale-video-studio`
2. Go to **Settings** → **Pages**
3. Configure:
   - **Source**: Deploy from a branch
   - **Branch**: `main` / `/(root)` 
   - **Folder**: `/frontend`
4. Click "Save"
5. Wait 2-3 minutes for deployment

### Step 2: Access the App
Your app will be available at: `https://barksdale410.github.io/barksdale-video-studio/`

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/api/health` | GET | Health check |
| `/api/options` | GET | Get directors, genres, moods |
| `/api/directors` | GET | Get all director details |
| `/api/directors/{name}` | GET | Get specific director |
| `/api/script/analyze` | POST | Analyze script and generate storyboard |
| `/api/video/generate` | POST | Generate video from storyboard |

### Example Script Analysis Request
```bash
curl -X POST https://your-backend.onrender.com/api/script/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "script": "INT. STUDIO - NIGHT\n\nA producer works.",
    "director": "Hype Williams",
    "genre": "Drama",
    "mood": "Cinematic"
  }'
```

---

## Using the App

1. Open the frontend URL
2. Enter your backend API URL in the API Endpoint field
3. Select a director, genre, and mood
4. Paste your script
5. Click "Analyze Script" to generate a storyboard
6. Click "Generate Movie" to create the video

---

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

### Frontend
Simply open `frontend/index.html` in a browser (or use a local server).
Set the API URL to `http://localhost:8001` in the app.