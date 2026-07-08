from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============ USER SCHEMAS ============

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    preferred_dark_mode: Optional[bool] = None
    favorite_directors: Optional[List[int]] = None


class UserResponse(UserBase):
    id: int
    is_premium: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============ DIRECTOR SCHEMAS ============

class DirectorBase(BaseModel):
    name: str
    bio: Optional[str] = None
    country: Optional[str] = None
    birth_year: Optional[int] = None
    
    color_palette: List[str] = []
    camera_style: Optional[str] = None
    lighting_style: Optional[str] = None
    editing_style: Optional[str] = None
    sound_style: Optional[str] = None
    visual_signature: Optional[str] = None
    moods: List[str] = []
    genres: List[str] = []
    popularity_score: float = 0.0
    image_url: Optional[str] = None
    film_count: int = 0


class DirectorCreate(DirectorBase):
    tmdb_id: Optional[int] = None


class DirectorResponse(DirectorBase):
    id: int
    tmdb_id: Optional[int] = None
    is_featured: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class DirectorListResponse(BaseModel):
    directors: List[DirectorResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class DirectorProfileResponse(DirectorResponse):
    """Extended director profile with all details."""
    death_year: Optional[int] = None
    tmdb_url: Optional[str] = None
    generations_count: Optional[int] = None
    user_favorite: Optional[bool] = None


# ============ SCRIPT ANALYSIS SCHEMAS ============

class SceneResponse(BaseModel):
    scene_number: int
    heading: str
    action: str
    duration: int
    emotional_tone: str
    director_style: Optional[str] = None
    color_palette: List[str] = []
    camera: Optional[str] = None
    lighting: Optional[str] = None
    editing: Optional[str] = None
    transitions: Optional[str] = None


class ScriptAnalysisRequest(BaseModel):
    script: str = Field(..., min_length=10, max_length=50000)
    director_id: Optional[int] = None
    director_name: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    use_cache: bool = True


class ScriptAnalysisResponse(BaseModel):
    scenes: List[SceneResponse]
    total_duration: int
    scene_count: int
    themes: List[str] = []
    genre: Optional[str] = None
    mood: Optional[str] = None
    cached: bool = False
    analysis_id: Optional[int] = None


# ============ VIDEO GENERATION SCHEMAS ============

class VideoGenerationRequest(BaseModel):
    script: str = Field(..., min_length=10, max_length=50000)
    director_id: int
    genre: Optional[str] = None
    mood: Optional[str] = None
    analysis_id: Optional[int] = None  # Use cached analysis


class GenerationResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    error_message: Optional[str] = None
    estimated_duration: Optional[int] = None
    created_at: datetime


class GenerationStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    error_message: Optional[str] = None
    estimated_duration: Optional[int] = None
    analysis_result: Optional[dict] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============ GENERATION HISTORY SCHEMAS ============

class GenerationHistoryItem(BaseModel):
    id: int
    job_id: str
    status: str
    director_name: str
    thumbnail_url: Optional[str] = None
    scene_count: int
    estimated_duration: Optional[int] = None
    created_at: datetime


class GenerationHistoryResponse(BaseModel):
    generations: List[GenerationHistoryItem]
    total: int
    page: int
    limit: int


# ============ FAVORITE DIRECTOR SCHEMAS ============

class FavoriteDirectorAdd(BaseModel):
    director_id: int
    notes: Optional[str] = None


class FavoriteDirectorResponse(BaseModel):
    id: int
    director: DirectorResponse
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ FILTER SCHEMAS ============

class DirectorFilters(BaseModel):
    letter: Optional[str] = None  # A-Z
    genre: Optional[str] = None
    mood: Optional[str] = None
    country: Optional[str] = None
    decade: Optional[int] = None  # 1970, 1980, 1990, etc.
    search: Optional[str] = None
    is_featured: Optional[bool] = None
    page: int = 1
    limit: int = 50


# ============ PAGINATION SCHEMAS ============

class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    limit: int
    total_pages: int


# ============ ERROR SCHEMAS ============

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class RateLimitError(BaseModel):
    detail: str = "Rate limit exceeded"
    limit: int
    resets_at: Optional[datetime] = None
