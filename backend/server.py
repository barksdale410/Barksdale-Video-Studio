# backend/server.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import uvicorn
import os
import re
from typing import List, Optional

app = FastAPI(title="Barksdale Video Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load templates from the parent directory (../templates/)
with open(os.path.join(BASE_DIR, '..', 'templates', 'directors.json'), 'r') as f:
    DIRECTORS = json.load(f).get('directors', [])

with open(os.path.join(BASE_DIR, '..', 'templates', 'genres.json'), 'r') as f:
    GENRES = json.load(f).get('genres', [])

with open(os.path.join(BASE_DIR, '..', 'templates', 'moods.json'), 'r') as f:
    MOODS_DATA = json.load(f)
    MOODS = MOODS_DATA.get('moods', [])


class ScriptAnalysisRequest(BaseModel):
    script: str
    director: str
    genre: str
    mood: str


class VideoGenerationRequest(BaseModel):
    storyboard: List[dict]
    director: str


def analyze_script_content(script: str, director: str, genre: str, mood: str) -> dict:
    """Analyze script and generate storyboard scenes."""
    # Find the director info
    director_info = next((d for d in DIRECTORS if d['name'] == director), DIRECTORS[0])
    
    # Parse scenes from script
    scenes = []
    lines = script.strip().split('\n')
    current_scene = None
    current_action = []
    scene_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Scene heading detection (INT., EXT., INT/EXT.)
        if re.match(r'^(INT\.|EXT\.|INT/EXT\.)', line, re.IGNORECASE):
            if current_scene:
                scenes.append({
                    "scene_number": scene_count,
                    "heading": current_scene,
                    "action": ' '.join(current_action),
                    "duration": 8 + len(current_action) * 2,
                    "emotional_tone": mood,
                    "director_style": director_info['style'],
                    "color_palette": director_info['color_palette'],
                    "camera": director_info['camera'],
                    "lighting": director_info['lighting'],
                    "editing": director_info['editing'],
                    "transitions": director_info['transitions']
                })
                current_action = []
            
            scene_count += 1
            current_scene = line
        elif line.startswith('PRODUCER') or line.startswith('CHARACTER') or line.startswith('NARRATOR'):
            # Dialogue line
            continue
        elif line.startswith('('):
            # Parenthetical
            continue
        else:
            current_action.append(line)
    
    # Add last scene
    if current_scene:
        scenes.append({
            "scene_number": scene_count,
            "heading": current_scene,
            "action": ' '.join(current_action),
            "duration": 8 + len(current_action) * 2,
            "emotional_tone": mood,
            "director_style": director_info['style'],
            "color_palette": director_info['color_palette'],
            "camera": director_info['camera'],
            "lighting": director_info['lighting'],
            "editing": director_info['editing'],
            "transitions": director_info['transitions']
        })
    
    # Fallback if no scenes parsed
    if not scenes:
        scenes.append({
            "scene_number": 1,
            "heading": "INT. STUDIO - NIGHT",
            "action": script[:200],
            "duration": 15,
            "emotional_tone": mood,
            "director_style": director_info['style'],
            "color_palette": director_info['color_palette'],
            "camera": director_info['camera'],
            "lighting": director_info['lighting'],
            "editing": director_info['editing'],
            "transitions": director_info['transitions']
        })
    
    return {
        "scenes": scenes,
        "total_duration": sum(s['duration'] for s in scenes),
        "scene_count": len(scenes),
        "director": director_info,
        "genre": genre,
        "mood": mood
    }


@app.get("/")
async def root():
    return {
        "message": "Barksdale Video Studio API is running",
        "version": "1.0.0",
        "endpoints": ["/api/options", "/api/script/analyze", "/api/video/generate", "/api/directors", "/api/health"]
    }


@app.get("/api/options")
async def options():
    """Get available options for directors, genres, and moods."""
    return {
        "directors": [d.get('name') for d in DIRECTORS],
        "genres": [g.get('name') for g in GENRES],
        "moods": MOODS
    }


@app.get("/api/directors")
async def get_directors():
    """Get all director details."""
    return {"directors": DIRECTORS}


@app.get("/api/directors/{director_name}")
async def get_director(director_name: str):
    """Get specific director details."""
    director = next((d for d in DIRECTORS if d['name'].lower() == director_name.lower()), None)
    if director:
        return director
    return {"error": "Director not found"}


@app.post("/api/script/analyze")
async def analyze_script(request: ScriptAnalysisRequest):
    """Analyze a script and generate a storyboard."""
    result = analyze_script_content(
        script=request.script,
        director=request.director,
        genre=request.genre,
        mood=request.mood
    )
    return result


@app.post("/api/video/generate")
async def generate_video(request: VideoGenerationRequest):
    """Generate video based on storyboard."""
    director_info = next((d for d in DIRECTORS if d['name'] == request.director), DIRECTORS[0])
    
    # In a real implementation, this would trigger video generation
    return {
        "status": "success",
        "message": "Video generation initiated",
        "video_id": f"vid_{os.urandom(8).hex()}",
        "director_style": director_info['style'],
        "scenes_count": len(request.storyboard),
        "estimated_duration": sum(s.get('duration', 10) for s in request.storyboard),
        "render_url": f"https://render.barksdale.video/videos/{os.urandom(8).hex()}.mp4"
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Barksdale Video Studio API"}


@app.get("/api/genres")
async def get_genres():
    """Get all genres."""
    return {"genres": GENRES}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
