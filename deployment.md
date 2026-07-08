# Deployment Guide

## Backend (Render)
1. Go to render.com
2. Create Web Service → connect barksdale410/barksdale-video-studio
3. Build Command: pip install -r backend/requirements.txt
4. Start Command: uvicorn backend.server:app --host 0.0.0.0 --port 8001

## Frontend (GitHub Pages)
1. Enable Pages → branch: main, folder: frontend/
2. URL: https://barksdale410.github.io/barksdale-video-studio/