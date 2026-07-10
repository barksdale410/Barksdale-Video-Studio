import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_optional_user
from app.core.config import settings
from app.models.models import Director, Generation, User
from app.schemas.schemas import VideoGenerationRequest, GenerationResponse, GenerationStatusResponse
from backend.video_engine import VideoGenerator

router = APIRouter(prefix="/api/v1", tags=["Video Generation"])


@router.post("/generate", response_model=GenerationResponse)
async def start_video_generation(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    user_id: Optional[int] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Start a video generation job."""
    # Validate director
    director = db.query(Director).filter(Director.id == request.director_id).first()
    if not director:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director not found"
        )
    
    # Check rate limit for authenticated users
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user and not user.is_premium:
            today = datetime.utcnow().date()
            if user.daily_generation_count >= settings.FREE_TIER_GENERATIONS_PER_DAY:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily limit reached. Free tier allows {settings.FREE_TIER_GENERATIONS_PER_DAY} generations per day."
                )
    
    # Create generation job
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    generation = Generation(
        job_id=job_id,
        user_id=user_id,
        director_id=request.director_id,
        script_content=request.script[:5000],  # Store truncated
        script_hash=hash(request.script) % (10**12),
        status="pending",
        progress=0,
        current_step="Queued"
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)
    
    # Update user rate limit
    if user_id and user:
        user.daily_generation_count += 1
        user.last_generation_date = datetime.utcnow()
        db.commit()
    
    # Queue the job (in production, this goes to Celery)
    # For now, we'll process it in background
    background_tasks.add_task(process_video_generation, job_id, db)
    
    return GenerationResponse(
        job_id=job_id,
        status="pending",
        progress=0,
        current_step="Queued",
        created_at=generation.created_at
    )


def process_video_generation(job_id: str, db: Session):
    """Process video generation job using NVIDIA Cosmos3-Nano via Hugging Face."""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    video_generator = VideoGenerator()
    
    try:
        generation = db.query(Generation).filter(Generation.job_id == job_id).first()
        if not generation:
            return
        
        # Update status to processing
        generation.status = "processing"
        generation.started_at = datetime.utcnow()
        generation.current_step = "Parsing"
        generation.progress = 10
        db.commit()
        
        # Step 1: Parsing (20%)
        import time
        time.sleep(0.5)
        generation.progress = 20
        generation.current_step = "Theming"
        db.commit()
        
        # Step 2: Theming (40%)
        time.sleep(0.5)
        generation.progress = 40
        generation.current_step = "Styling"
        db.commit()
        
        # Step 3: Styling (60%)
        time.sleep(0.5)
        generation.progress = 60
        generation.current_step = "Generating video"
        db.commit()
        
        # Step 4: Generate video using NVIDIA Cosmos3-Nano
        script_content = generation.script_content
        result = video_generator.generate_scene(
            prompt=script_content[:500],  # Limit prompt length
            duration=5  # 5 seconds per scene
        )
        
        generation.progress = 90
        generation.current_step = "Finalizing"
        db.commit()
        
        # Step 5: Finalize
        if result.get('success'):
            generation.status = "completed"
            generation.progress = 100
            generation.current_step = "Ready"
            generation.completed_at = datetime.utcnow()
            generation.video_url = result.get('video_url', f"https://example.com/videos/{job_id}.mp4")
            generation.thumbnail_url = f"https://picsum.photos/seed/{job_id}/640/360"
            generation.estimated_duration = result.get('duration', 5)
        else:
            generation.status = "failed"
            generation.error_message = result.get('error', 'Video generation failed')
            generation.completed_at = datetime.utcnow()
        
        db.commit()
        
    except Exception as e:
        generation = db.query(Generation).filter(Generation.job_id == job_id).first()
        if generation:
            generation.status = "failed"
            generation.error_message = str(e)
            generation.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


@router.get("/jobs/{job_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(
    job_id: str,
    user_id: Optional[int] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get status of a generation job."""
    generation = db.query(Generation).filter(Generation.job_id == job_id).first()
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if generation.user_id and generation.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return GenerationStatusResponse(
        job_id=generation.job_id,
        status=generation.status,
        progress=generation.progress,
        current_step=generation.current_step,
        video_url=generation.video_url,
        thumbnail_url=generation.thumbnail_url,
        error_message=generation.error_message,
        estimated_duration=generation.estimated_duration,
        analysis_result=generation.analysis_result,
        created_at=generation.created_at,
        started_at=generation.started_at,
        completed_at=generation.completed_at
    )


@router.get("/jobs/{job_id}")
async def get_generation(
    job_id: str,
    user_id: Optional[int] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get full generation details."""
    generation = db.query(Generation).filter(Generation.job_id == job_id).first()
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if generation.user_id and generation.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    director = db.query(Director).filter(Director.id == generation.director_id).first()
    
    return {
        "job_id": generation.job_id,
        "status": generation.status,
        "progress": generation.progress,
        "current_step": generation.current_step,
        "video_url": generation.video_url,
        "thumbnail_url": generation.thumbnail_url,
        "error_message": generation.error_message,
        "estimated_duration": generation.estimated_duration,
        "script_content": generation.script_content[:500] + "..." if len(generation.script_content) > 500 else generation.script_content,
        "director": {
            "id": director.id,
            "name": director.name,
            "style": director.visual_signature
        } if director else None,
        "created_at": generation.created_at,
        "completed_at": generation.completed_at
    }


@router.get("/generations/history")
async def get_generation_history(
    page: int = 1,
    limit: int = 20,
    user_id: int = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get user's generation history."""
    if not user_id:
        return {"generations": [], "total": 0}
    
    query = db.query(Generation).filter(Generation.user_id == user_id)
    total = query.count()
    
    generations = query.order_by(Generation.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()
    
    result = []
    for g in generations:
        director = db.query(Director).filter(Director.id == g.director_id).first()
        result.append({
            "id": g.id,
            "job_id": g.job_id,
            "status": g.status,
            "progress": g.progress,
            "video_url": g.video_url,
            "thumbnail_url": g.thumbnail_url,
            "director_name": director.name if director else "Unknown",
            "scene_count": len(g.analysis_result.get("scenes", [])) if g.analysis_result else 0,
            "estimated_duration": g.estimated_duration,
            "created_at": g.created_at,
            "completed_at": g.completed_at
        })
    
    return {
        "generations": result,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.delete("/jobs/{job_id}")
async def cancel_generation(
    job_id: str,
    user_id: int = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending generation job."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    generation = db.query(Generation).filter(
        Generation.job_id == job_id,
        Generation.user_id == user_id
    ).first()
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if generation.status not in ["pending", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel job in current status"
        )
    
    generation.status = "cancelled"
    generation.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Job cancelled"}
