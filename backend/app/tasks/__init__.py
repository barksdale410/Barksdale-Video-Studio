from app.tasks.video_tasks import (
    celery_app,
    generate_video,
    generate_video_simple,
    cleanup_old_jobs,
    update_daily_stats
)

__all__ = [
    "celery_app",
    "generate_video",
    "generate_video_simple",
    "cleanup_old_jobs",
    "update_daily_stats"
]
