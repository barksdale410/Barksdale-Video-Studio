import hashlib
import random
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_optional_user
from app.models.models import Director, FavoriteDirector
from app.schemas.schemas import (
    DirectorResponse, DirectorListResponse, DirectorProfileResponse,
    DirectorFilters, FavoriteDirectorAdd, FavoriteDirectorResponse
)

router = APIRouter(prefix="/api/v1/directors", tags=["Directors"])


def apply_filters(query: Query, filters: DirectorFilters, db: Session) -> Query:
    """Apply filters to director query."""
    if filters.letter:
        query = query.filter(Director.name.ilike(f"{filters.letter}%"))
    
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(
            or_(
                Director.name.ilike(search_term),
                Director.bio.ilike(search_term),
                Director.country.ilike(search_term)
            )
        )
    
    if filters.genre:
        query = query.filter(Director.genres.contains([filters.genre]))
    
    if filters.mood:
        query = query.filter(Director.moods.contains([filters.mood]))
    
    if filters.country:
        query = query.filter(Director.country.ilike(f"%{filters.country}%"))
    
    if filters.decade:
        start_year = filters.decade
        end_year = start_year + 9
        query = query.filter(
            and_(
                Director.birth_year >= start_year,
                Director.birth_year <= end_year
            )
        )
    
    if filters.is_featured is not None:
        query = query.filter(Director.is_featured == filters.is_featured)
    
    return query


@router.get("", response_model=DirectorListResponse)
async def list_directors(
    letter: Optional[str] = Query(None, description="Filter by starting letter (A-Z)"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    mood: Optional[str] = Query(None, description="Filter by mood"),
    country: Optional[str] = Query(None, description="Filter by country"),
    decade: Optional[int] = Query(None, description="Filter by birth decade (e.g., 1970)"),
    search: Optional[str] = Query(None, description="Search by name, bio, or country"),
    featured: Optional[bool] = Query(None, description="Only featured directors"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("popularity_score", description="Sort by: popularity_score, name, film_count"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db)
):
    """Get paginated list of directors with filters."""
    filters = DirectorFilters(
        letter=letter, genre=genre, mood=mood, country=country,
        decade=decade, search=search, is_featured=featured,
        page=page, limit=limit
    )
    
    # Base query
    query = db.query(Director)
    
    # Apply filters
    query = apply_filters(query, filters, db)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Director, sort_by, Director.popularity_score)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    offset = (page - 1) * limit
    directors = query.offset(offset).limit(limit).all()
    
    return DirectorListResponse(
        directors=[DirectorResponse.model_validate(d) for d in directors],
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/letters")
async def get_letters(db: Session = Depends(get_db)):
    """Get all available starting letters."""
    # Get first letter of each director name
    letters = db.query(
        func.upper(func.left(Director.name, 1)).label('letter')
    ).distinct().all()
    
    available_letters = sorted(set([l[0] for l in letters if l[0]]))
    return {"letters": available_letters}


@router.get("/genres")
async def get_genres(db: Session = Depends(get_db)):
    """Get all unique genres across directors."""
    genres = db.query(Director.genres).distinct().all()
    all_genres = set()
    for g in genres:
        if g[0]:
            all_genres.update(g[0])
    return {"genres": sorted(all_genres)}


@router.get("/moods")
async def get_moods(db: Session = Depends(get_db)):
    """Get all unique moods across directors."""
    moods = db.query(Director.moods).distinct().all()
    all_moods = set()
    for m in moods:
        if m[0]:
            all_moods.update(m[0])
    return {"moods": sorted(all_moods)}


@router.get("/countries")
async def get_countries(db: Session = Depends(get_db)):
    """Get all unique countries."""
    countries = db.query(Director.country).filter(
        Director.country.isnot(None)
    ).distinct().order_by(Director.country).all()
    return {"countries": [c[0] for c in countries if c[0]]}


@router.get("/random", response_model=DirectorResponse)
async def get_random_director(
    genre: Optional[str] = Query(None),
    mood: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get a random director, optionally filtered."""
    query = db.query(Director)
    
    if genre:
        query = query.filter(Director.genres.contains([genre]))
    if mood:
        query = query.filter(Director.moods.contains([mood]))
    
    directors = query.all()
    if not directors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No directors found matching criteria"
        )
    
    return DirectorResponse.model_validate(random.choice(directors))


@router.get("/{director_id}", response_model=DirectorProfileResponse)
async def get_director(
    director_id: int,
    user_id: Optional[int] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get detailed director profile."""
    director = db.query(Director).filter(Director.id == director_id).first()
    
    if not director:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director not found"
        )
    
    # Check if user has favorited
    is_favorite = False
    if user_id:
        favorite = db.query(FavoriteDirector).filter(
            FavoriteDirector.user_id == user_id,
            FavoriteDirector.director_id == director_id
        ).first()
        is_favorite = favorite is not None
    
    response = DirectorProfileResponse(
        **{**DirectorResponse.model_validate(director).model_dump(), 
           "user_favorite": is_favorite}
    )
    return response


@router.get("/by-name/{name}", response_model=DirectorResponse)
async def get_director_by_name(
    name: str,
    db: Session = Depends(get_db)
):
    """Get director by exact name."""
    director = db.query(Director).filter(
        func.lower(Director.name) == name.lower()
    ).first()
    
    if not director:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Director '{name}' not found"
        )
    
    return DirectorResponse.model_validate(director)


# ============ FAVORITES ============

@router.get("/favorites/me", response_model=List[FavoriteDirectorResponse])
async def get_my_favorites(
    user_id: int = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get user's favorite directors."""
    if not user_id:
        return []
    
    favorites = db.query(FavoriteDirector).filter(
        FavoriteDirector.user_id == user_id
    ).all()
    
    return [FavoriteDirectorResponse.model_validate(f) for f in favorites]


@router.post("/favorites", response_model=FavoriteDirectorResponse)
async def add_favorite(
    data: FavoriteDirectorAdd,
    user_id: int = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Add director to favorites."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check director exists
    director = db.query(Director).filter(Director.id == data.director_id).first()
    if not director:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director not found"
        )
    
    # Check if already favorited
    existing = db.query(FavoriteDirector).filter(
        FavoriteDirector.user_id == user_id,
        FavoriteDirector.director_id == data.director_id
    ).first()
    
    if existing:
        return FavoriteDirectorResponse.model_validate(existing)
    
    # Create favorite
    favorite = FavoriteDirector(
        user_id=user_id,
        director_id=data.director_id,
        notes=data.notes
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    
    return FavoriteDirectorResponse.model_validate(favorite)


@router.delete("/favorites/{director_id}")
async def remove_favorite(
    director_id: int,
    user_id: int = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Remove director from favorites."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    favorite = db.query(FavoriteDirector).filter(
        FavoriteDirector.user_id == user_id,
        FavoriteDirector.director_id == director_id
    ).first()
    
    if favorite:
        db.delete(favorite)
        db.commit()
    
    return {"message": "Removed from favorites"}
