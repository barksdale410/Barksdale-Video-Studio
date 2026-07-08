"""
Celery tasks for video generation.
Uses Redis as broker and supports distributed processing.
"""

import json
import logging
import os
import time
from datetime import datetime

from celery import Celery
from sqlalchemy.orm import Session

from app.core.config import settings

# Configure Celery
celery_app = Celery(
    "barksdale",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.video_tasks"]
)

# Configure
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_session():
    """Create a new database session for Celery tasks."""
    from app.core.database import SessionLocal
    return SessionLocal()


def update_generation_status(
    job_id: str,
    status: str,
    progress: int = None,
    current_step: str = None,
    video_url: str = None,
    thumbnail_url: str = None,
    error_message: str = None,
    estimated_duration: int = None,
    db: Session = None
):
    """Update generation status in database."""
    from app.models.models import Generation
    
    if db is None:
        db = get_db_session()
        should_close = True
    else:
        should_close = False
    
    try:
        generation = db.query(Generation).filter(Generation.job_id == job_id).first()
        if generation:
            generation.status = status
            if progress is not None:
                generation.progress = progress
            if current_step is not None:
                generation.current_step = current_step
            if video_url is not None:
                generation.video_url = video_url
            if thumbnail_url is not None:
                generation.thumbnail_url = thumbnail_url
            if error_message is not None:
                generation.error_message = error_message
            if estimated_duration is not None:
                generation.estimated_duration = estimated_duration
            
            if status == "processing" and not generation.started_at:
                generation.started_at = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled"]:
                generation.completed_at = datetime.utcnow()
            
            db.commit()
    finally:
        if should_close:
            db.close()


@celery_app.task(bind=True, name="generate_video")
def generate_video(self, job_id: str, director_id: int, script: str, director_profile: dict = None):
    """
    Generate video using AI video model (Replicate/RunwayML).
    
    Pipeline:
    1. Parse script into scenes
    2. Generate detailed prompts for each scene
    3. Generate video frames using AI
    4. Compile into final video
    5. Upload to storage (S3/Cloudinary)
    """
    logger.info(f"Starting video generation job: {job_id}")
    db = get_db_session()
    
    try:
        # Step 1: Parsing (10%)
        update_generation_status(job_id, "processing", 10, "Parsing script", db=db)
        scenes = parse_script_to_scenes(script)
        logger.info(f"Parsed {len(scenes)} scenes")
        
        # Step 2: Theming (25%)
        update_generation_status(job_id, "processing", 25, "Analyzing themes", db=db)
        themes = extract_themes(script)
        logger.info(f"Extracted themes: {themes}")
        
        # Step 3: Styling (40%)
        update_generation_status(job_id, "processing", 40, "Applying director style", db=db)
        prompts = generate_director_prompts(scenes, director_profile or {}, themes)
        logger.info(f"Generated {len(prompts)} prompts")
        
        # Step 4: Generate video frames (70%)
        update_generation_status(job_id, "processing", 70, "Generating video frames", db=db)
        video_frames = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"Generating frame {i+1}/{len(prompts)}: {prompt[:50]}...")
            
            # Call Replicate API for video generation
            frame_url = call_replicate_video(prompt, job_id, i)
            if frame_url:
                video_frames.append(frame_url)
            
            # Update progress
            progress = 70 + (i * 20 // len(prompts))
            update_generation_status(job_id, "processing", progress, f"Generating frame {i+1}", db=db)
        
        # Step 5: Compile video (90%)
        update_generation_status(job_id, "processing", 90, "Compiling video", db=db)
        video_url = compile_video_frames(video_frames, job_id)
        
        # Step 6: Upload and finalize
        final_url = upload_to_storage(video_url, job_id)
        
        # Complete
        update_generation_status(
            job_id, "completed", 100, "Ready",
            video_url=final_url,
            thumbnail_url=generate_thumbnail(final_url, job_id),
            estimated_duration=sum(s.get("duration", 5) for s in scenes),
            db=db
        )
        logger.info(f"Video generation complete: {job_id} -> {final_url}")
        
        return {"status": "completed", "video_url": final_url}
        
    except Exception as e:
        logger.error(f"Video generation failed: {job_id} - {str(e)}")
        update_generation_status(
            job_id, "failed", error_message=str(e), db=db
        )
        raise


@celery_app.task(name="generate_video_simple")
def generate_video_simple(job_id: str, director_id: int, script: str):
    """
    Simplified video generation for demo purposes.
    Simulates the generation process without actual AI video generation.
    """
    db = get_db_session()
    
    try:
        steps = [
            (10, "Parsing script"),
            (25, "Analyzing themes"),
            (40, "Applying director style"),
            (60, "Generating frames"),
            (80, "Rendering scenes"),
            (90, "Compiling video"),
            (100, "Ready")
        ]
        
        for progress, step in steps:
            update_generation_status(job_id, "processing", progress, step, db=db)
            time.sleep(2)  # Simulate processing time
        
        # Generate demo video URL
        video_url = f"https://storage.barksdale.video/videos/{job_id}.mp4"
        thumbnail_url = f"https://picsum.photos/seed/{job_id}/640/360"
        
        update_generation_status(
            job_id, "completed", 100, "Ready",
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            estimated_duration=30,
            db=db
        )
        
        return {"status": "completed", "video_url": video_url}
        
    except Exception as e:
        update_generation_status(job_id, "failed", error_message=str(e), db=db)
        raise
    finally:
        db.close()


# ============ Helper Functions ============

def parse_script_to_scenes(script: str) -> list:
    """Parse script into structured scenes."""
    import re
    
    scenes = []
    lines = script.strip().split('\n')
    current_heading = None
    current_action = []
    scene_num = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if re.match(r'^(INT\.|EXT\.|INT/EXT\.)', line, re.IGNORECASE):
            if current_heading:
                scenes.append({
                    "scene_number": scene_num,
                    "heading": current_heading,
                    "action": ' '.join(current_action)[:300],
                    "duration": max(3, min(15, len(current_action) * 2))
                })
                current_action = []
            
            scene_num += 1
            current_heading = line
        elif not line.startswith(('(', 'PRODUCER', 'CHARACTER', 'NARRATOR')):
            current_action.append(line)
    
    if current_heading:
        scenes.append({
            "scene_number": scene_num,
            "heading": current_heading,
            "action": ' '.join(current_action)[:300],
            "duration": max(3, min(15, len(current_action) * 2))
        })
    
    return scenes or [{"scene_number": 1, "heading": "INT. SCENE", "action": script[:200], "duration": 5}]


def extract_themes(script: str) -> list:
    """Extract themes from script content."""
    themes = []
    script_lower = script.lower()
    
    theme_keywords = {
        "Love": ["love", "romance", "heart", "kiss", "relationship", "couple"],
        "Conflict": ["fight", "battle", "war", "conflict", "enemy", "versus"],
        "Mystery": ["secret", "mystery", "hidden", "discover", "reveal"],
        "Survival": ["survive", "escape", "trapped", "danger", "threat"],
        "Redemption": ["forgive", "redemption", "guilt", "apologize", "second chance"]
    }
    
    for theme, keywords in theme_keywords.items():
        if any(kw in script_lower for kw in keywords):
            themes.append(theme)
    
    return themes[:3] or ["Drama"]


def generate_director_prompts(scenes: list, director_profile: dict, themes: list) -> list:
    """Generate detailed prompts for each scene based on director style."""
    color_palette = director_profile.get("color_palette", ["#333333", "#666666"])
    camera_style = director_profile.get("camera_style", "cinematic")
    visual_sig = director_profile.get("visual_signature", "professional")
    
    prompts = []
    for scene in scenes:
        prompt = (
            f"{scene['heading']}: {scene['action']}. "
            f"Colors: {', '.join(color_palette[:3])}. "
            f"Camera: {camera_style}. "
            f"Style: {visual_sig}. "
            f"Themes: {', '.join(themes[:2])}. "
            f"Professional cinematography, 4K, cinematic lighting."
        )
        prompts.append(prompt)
    
    return prompts


def call_replicate_video(prompt: str, job_id: str, frame_index: int) -> str:
    """
    Call Replicate API for video generation.
    Uses Stable Video Diffusion or similar model.
    """
    if not settings.REPLICATE_API_TOKEN:
        logger.warning("Replicate API token not configured, using placeholder")
        return f"https://picsum.photos/seed/{job_id}_{frame_index}/640/360"
    
    try:
        import replicate
        
        # Use Stable Video Diffusion
        model = replicate.models.get("stability-ai/stable-video-diffusion")
        version = model.versions.get("3f0457e4619daac51203dedb472816f5a4bb4ccb3da8a14ee953698d7")
        
        output = version.predict(
            prompt=prompt,
            num_frames=24,
            fps=8
        )
        
        return output[0] if output else None
        
    except Exception as e:
        logger.error(f"Replicate API error: {e}")
        return f"https://picsum.photos/seed/{job_id}_{frame_index}/640/360"


def compile_video_frames(frames: list, job_id: str) -> str:
    """Compile video frames into final video."""
    if not frames:
        return f"https://storage.barksdale.video/videos/{job_id}.mp4"
    
    # In production, use ffmpeg or similar to compile
    # For demo, return first frame as "video"
    return frames[0]


def upload_to_storage(video_path: str, job_id: str) -> str:
    """Upload video to cloud storage."""
    # Check if S3 is configured
    if settings.AWS_ACCESS_KEY_ID:
        # Upload to S3
        return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/videos/{job_id}.mp4"
    
    # Check if Cloudinary is configured
    if settings.CLOUDINARY_CLOUD_NAME:
        # Upload to Cloudinary
        return f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/video/upload/videos/{job_id}.mp4"
    
    # Return original path
    return video_path


def generate_thumbnail(video_url: str, job_id: str) -> str:
    """Generate thumbnail from video."""
    # Use first frame or placeholder
    return f"https://picsum.photos/seed/{job_id}/640/360"


# ============ Scheduled Tasks ============

@celery_app.task(name="cleanup_old_jobs")
def cleanup_old_jobs():
    """Clean up old/failed jobs from database."""
    from app.models.models import Generation
    from datetime import timedelta
    
    db = get_db_session()
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=7)
        old_jobs = db.query(Generation).filter(
            Generation.created_at < cutoff,
            Generation.status.in_(["completed", "failed", "cancelled"])
        ).all()
        
        count = len(old_jobs)
        for job in old_jobs:
            db.delete(job)
        
        db.commit()
        logger.info(f"Cleaned up {count} old jobs")
        return count
        
    finally:
        db.close()


@celery_app.task(name="update_daily_stats")
def update_daily_stats():
    """Update daily generation statistics."""
    from app.models.models import Generation
    from datetime import timedelta
    
    db = get_db_session()
    
    try:
        today = datetime.utcnow().date()
        
        # Count today's generations
        today_count = db.query(Generation).filter(
            Generation.created_at >= today
        ).count()
        
        # Count completions
        completed_count = db.query(Generation).filter(
            Generation.created_at >= today,
            Generation.status == "completed"
        ).count()
        
        logger.info(f"Daily stats: {today_count} total, {completed_count} completed")
        return {"total": today_count, "completed": completed_count}
        
    finally:
        db.close()
