from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import uvicorn
import os

app = FastAPI(title="Barksdale Video Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, '..', 'templates', 'directors.json'), 'r') as f:
    DIRECTORS = json.load(f).get('directors', [])

with open(os.path.join(BASE_DIR, '..', 'templates', 'genres.json'), 'r') as f:
    GENRES = json.load(f).get('genres', [])

with open(os.path.join(BASE_DIR, '..', 'templates', 'moods.json'), 'r') as f:
    MOODS = json.load(f)

@app.get("/")
async def root():
    return {"message": "Barksdale Video Studio API is running"}

@app.get("/api/options")
async def options():
    return {
        "directors": [d.get('name') for d in DIRECTORS],
        "genres": [g.get('name') for g in GENRES],
        "moods": MOODS
    }

@app.post("/api/script/analyze")
async def analyze_script(request: Request):
    await request.json()
    return {
        "scenes": [
            {"scene_number": 1, "heading": "INT. STUDIO - NIGHT", "action": "A producer sits at a mixing console", "duration": 10, "emotional_tone": "Dark"}
        ],
        "total_duration": 10,
        "scene_count": 1
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
