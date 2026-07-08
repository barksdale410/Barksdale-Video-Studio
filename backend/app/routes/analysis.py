import hashlib
import json
import re
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_optional_user
from app.core.config import settings
from app.models.models import Director, ScriptAnalysis, RateLimitLog
from app.schemas.schemas import ScriptAnalysisRequest, ScriptAnalysisResponse, SceneResponse

router = APIRouter(prefix="/api/v1", tags=["Script Analysis"])


def parse_script_scenes(script: str, director_name: str, mood: str, color_palette: list) -> list:
    """Parse script into scenes."""
    scenes = []
    lines = script.strip().split('\n')
    current_heading = None
    current_action = []
    scene_num = 0
    
    # Director-specific defaults
    camera_styles = {
        "Christopher Nolan": "Wide establishing shots, steady-cam, IMAX format",
        "Wes Anderson": "Symmetrical framing, tracking shots, centered composition",
        "Quentin Tarantino": "Close-ups, trunk shots, 360-degree pans",
        "Hype Williams": "Fisheye lens, low angles, dynamic movement",
        "Greta Gerwig": "Close-ups, natural framing, character-focused",
        "Jordan Peele": "Slow reveals, suspenseful framing, Steadicam"
    }
    
    default_camera = camera_styles.get(director_name, "Professional cinematography")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Scene heading detection
        if re.match(r'^(INT\.|EXT\.|INT/EXT\.)', line, re.IGNORECASE):
            if current_heading:
                # Save previous scene
                scenes.append({
                    "scene_number": scene_num,
                    "heading": current_heading,
                    "action": ' '.join(current_action)[:200],
                    "duration": max(5, min(30, len(current_action) * 3)),
                    "emotional_tone": mood,
                    "director_style": director_name,
                    "color_palette": color_palette[:4],
                    "camera": default_camera,
                    "lighting": "Dramatic" if mood in ["Dark", "Suspenseful", "Tense"] else "Natural",
                    "editing": "Slow builds" if mood in ["Dark", "Epic"] else "Dynamic cuts",
                    "transitions": "Dissolves"
                })
                current_action = []
            
            scene_num += 1
            current_heading = line
        elif not line.startswith(('(', 'PRODUCER', 'CHARACTER', 'NARRATOR', 'MAN', 'WOMAN')):
            current_action.append(line)
    
    # Add last scene
    if current_heading:
        scenes.append({
            "scene_number": scene_num,
            "heading": current_heading,
            "action": ' '.join(current_action)[:200],
            "duration": max(5, min(30, len(current_action) * 3)),
            "emotional_tone": mood,
            "director_style": director_name,
            "color_palette": color_palette[:4],
            "camera": default_camera,
            "lighting": "Dramatic" if mood in ["Dark", "Suspenseful", "Tense"] else "Natural",
            "editing": "Slow builds" if mood in ["Dark", "Epic"] else "Dynamic cuts",
            "transitions": "Dissolves"
        })
    
    # Fallback if no scenes parsed
    if not scenes:
        scenes.append({
            "scene_number": 1,
            "heading": "INT. STUDIO - DAY",
            "action": script[:200],
            "duration": 15,
            "emotional_tone": mood,
            "director_style": director_name,
            "color_palette": color_palette[:4],
            "camera": default_camera,
            "lighting": "Natural",
            "editing": "Standard",
            "transitions": "Dissolves"
        })
    
    return scenes


def check_rate_limit(user_id: Optional[int], is_premium: bool, db: Session) -> bool:
    """Check if user has exceeded rate limit."""
    if not user_id:
        return True  # No rate limit for anonymous
    
    if is_premium:
        return True  # Unlimited for premium
    
    today = date.today().isoformat()
    
    # Get or create rate limit log
    log = db.query(RateLimitLog).filter(
        RateLimitLog.user_id == user_id,
        RateLimitLog.date == today
    ).first()
    
    if not log:
        log = RateLimitLog(user_id=user_id, date=today, generation_count=0)
        db.add(log)
        db.commit()
    
    return log.generation_count < settings.FREE_TIER_GENERATIONS_PER_DAY


def increment_rate_limit(user_id: int, db: Session):
    """Increment rate limit counter."""
    today = date.today().isoformat()
    
    log = db.query(RateLimitLog).filter(
        RateLimitLog.user_id == user_id,
        RateLimitLog.date == today
    ).first()
    
    if log:
        log.generation_count += 1
    else:
        log = RateLimitLog(user_id=user_id, date=today, generation_count=1)
        db.add(log)
    
    db.commit()


def extract_themes(script: str) -> list:
    """Extract themes from script."""
    themes = []
    
    # Simple keyword-based theme detection
    script_lower = script.lower()
    
    theme_keywords = {
        "Love": ["love", "romance", "heart", "kiss", "relationship"],
        "Death": ["death", "die", "kill", "murder", "dead"],
        "Power": ["power", "control", "authority", "rule", "king"],
        "Redemption": ["redeem", "forgive", "guilt", "apologize", "sorry"],
        "Identity": ["who am i", "identity", "discover", "true self", "mask"],
        "Survival": ["survive", "escape", "run", "chase", "trapped"],
        "Revenge": ["revenge", "payback", "retribution", "hate", "destroy"],
        "Coming of Age": ["grow up", "mature", "learn", "teenager", "childhood"]
    }
    
    for theme, keywords in theme_keywords.items():
        if any(kw in script_lower for kw in keywords):
            themes.append(theme)
    
    return themes[:5] if themes else ["Drama"]


@router.post("/analyze", response_model=ScriptAnalysisResponse)
async def analyze_script(
    request: ScriptAnalysisRequest,
    user_id: Optional[int] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Analyze a script and generate storyboard scenes."""
    # Get director info
    director = None
    director_name = request.director_name or "Unknown"
    
    if request.director_id:
        director = db.query(Director).filter(Director.id == request.director_id).first()
        if director:
            director_name = director.name
    
    # Create script hash for caching
    script_hash = hashlib.md5(
        f"{request.script}{director_name}{request.mood}".encode()
    ).hexdigest()
    
    # Check cache
    if request.use_cache and user_id:
        cached = db.query(ScriptAnalysis).filter(
            ScriptAnalysis.script_hash == script_hash,
            ScriptAnalysis.user_id == user_id
        ).first()
        
        if cached:
            cached.used_count += 1
            db.commit()
            return ScriptAnalysisResponse(
                scenes=[SceneResponse(**s) for s in cached.scenes],
                total_duration=cached.estimated_length or sum(s.get("duration", 10) for s in cached.scenes),
                scene_count=cached.scene_count,
                themes=cached.themes or [],
                genre=cached.genre,
                mood=cached.mood,
                cached=True,
                analysis_id=cached.id
            )
    
    # Parse scenes
    color_palette = director.color_palette if director else ["#333333", "#666666", "#999999", "#0A0A0A"]
    scenes = parse_script_scenes(
        request.script,
        director_name,
        request.mood or "Cinematic",
        color_palette
    )
    
    # Extract themes
    themes = extract_themes(request.script)
    
    total_duration = sum(s["duration"] for s in scenes)
    
    # Save to cache if user is authenticated
    if user_id:
        analysis = ScriptAnalysis(
            user_id=user_id,
            script_content=request.script[:1000],
            script_hash=script_hash,
            scenes=scenes,
            themes=themes,
            estimated_length=total_duration,
            scene_count=len(scenes),
            director_id=request.director_id,
            genre=request.genre,
            mood=request.mood
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        analysis_id = analysis.id
    else:
        analysis_id = None
    
    return ScriptAnalysisResponse(
        scenes=[SceneResponse(**s) for s in scenes],
        total_duration=total_duration,
        scene_count=len(scenes),
        themes=themes,
        genre=request.genre,
        mood=request.mood,
        cached=False,
        analysis_id=analysis_id
    )


@router.get("/analysis/history")
async def get_analysis_history(
    page: int = 1,
    limit: int = 20,
    user_id: int = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get user's analysis history."""
    if not user_id:
        return {"analyses": [], "total": 0}
    
    query = db.query(ScriptAnalysis).filter(ScriptAnalysis.user_id == user_id)
    total = query.count()
    
    analyses = query.order_by(ScriptAnalysis.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()
    
    return {
        "analyses": [
            {
                "id": a.id,
                "scene_count": a.scene_count,
                "themes": a.themes,
                "created_at": a.created_at
            }
            for a in analyses
        ],
        "total": total,
        "page": page,
        "limit": limit
    }
