from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, ARRAY, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Director(Base):
    """Director model with full cinematic profile."""
    __tablename__ = "directors"
    
    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=False, index=True)
    bio = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    birth_year = Column(Integer, nullable=True)
    death_year = Column(Integer, nullable=True)
    
    # Cinematic profile
    color_palette = Column(JSON, default=list)  # ["#FF1493", "#00BFFF", ...]
    camera_style = Column(String(500), nullable=True)
    lighting_style = Column(String(500), nullable=True)
    editing_style = Column(String(500), nullable=True)
    sound_style = Column(String(500), nullable=True)
    visual_signature = Column(Text, nullable=True)
    moods = Column(ARRAY(String), default=list)  # ["Dark", "Cinematic", ...]
    genres = Column(ARRAY(String), default=list)  # ["Thriller", "Sci-Fi", ...]
    
    # Metadata
    popularity_score = Column(Float, default=0.0)
    image_url = Column(String(500), nullable=True)
    tmdb_url = Column(String(500), nullable=True)
    is_featured = Column(Boolean, default=False)
    film_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    generations = relationship("Generation", back_populates="director")
    favorites = relationship("FavoriteDirector", back_populates="director")


class User(Base):
    """User model with authentication and preferences."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Subscription
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # OAuth
    google_id = Column(String(255), unique=True, nullable=True)
    
    # Preferences
    preferred_dark_mode = Column(Boolean, default=True)
    favorite_directors = Column(ARRAY(Integer), default=list)
    
    # Rate limiting
    daily_generation_count = Column(Integer, default=0)
    last_generation_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    generations = relationship("Generation", back_populates="user")
    script_analyses = relationship("ScriptAnalysis", back_populates="user")
    favorites = relationship("FavoriteDirector", back_populates="user")
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
    )


class Generation(Base):
    """Video generation job tracking."""
    __tablename__ = "generations"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    director_id = Column(Integer, ForeignKey("directors.id"), nullable=False)
    
    # Script content
    script_content = Column(Text, nullable=False)
    script_hash = Column(String(64), index=True, nullable=True)  # For caching
    
    # Analysis results (cached)
    analysis_result = Column(JSON, nullable=True)
    
    # Generation status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100), nullable=True)  # "Parsing", "Theming", "Styling", "Ready"
    
    # Results
    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    estimated_duration = Column(Integer, nullable=True)  # seconds
    actual_duration = Column(Integer, nullable=True)
    generation_prompt = Column(Text, nullable=True)
    
    # Usage tracking
    tokens_used = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="generations")
    director = relationship("Director", back_populates="generations")
    
    __table_args__ = (
        Index('idx_generations_user', 'user_id'),
        Index('idx_generations_status', 'status'),
        Index('idx_generations_created', 'created_at'),
    )


class ScriptAnalysis(Base):
    """Cached script analysis results."""
    __tablename__ = "script_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Script
    script_content = Column(Text, nullable=False)
    script_hash = Column(String(64), index=True, nullable=False)
    
    # Analysis result
    scenes = Column(JSON, default=list)
    themes = Column(JSON, default=list)
    estimated_length = Column(Integer, nullable=True)
    scene_count = Column(Integer, default=0)
    
    # Analysis metadata
    director_id = Column(Integer, ForeignKey("directors.id"), nullable=True)
    genre = Column(String(100), nullable=True)
    mood = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="script_analyses")
    
    __table_args__ = (
        Index('idx_analysis_hash', 'script_hash'),
        Index('idx_analysis_user', 'user_id'),
    )


class FavoriteDirector(Base):
    """User's favorite directors."""
    __tablename__ = "favorite_directors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    director_id = Column(Integer, ForeignKey("directors.id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    director = relationship("Director", back_populates="favorites")
    
    __table_args__ = (
        Index('idx_favorite_user_director', 'user_id', 'director_id', unique=True),
    )


class RateLimitLog(Base):
    """Track API usage for rate limiting."""
    __tablename__ = "rate_limit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    generation_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_rate_limit_user_date', 'user_id', 'date', unique=True),
    )
