#!/usr/bin/env python3
"""
Seed script to populate the directors database.
Fetches directors from TMDB and generates style profiles using GPT-4o mini.

Usage:
    python scripts/seed_directors.py --full  # Fetch all directors
    python scripts/seed_directors.py --incremental  # Add new directors only
    python scripts/seed_directors.py --featured  # Just update featured directors
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional

import requests
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models.models import Director

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# TMDB API Configuration
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


class TMDbClient:
    """Client for TMDB API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def get_popular_directors(self, page: int = 1) -> Dict:
        """Get popular directors from TMDB."""
        url = f"{TMDB_BASE_URL}/person/popular"
        params = {"page": page, "language": "en-US"}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_movie_credits(self, person_id: int) -> Dict:
        """Get movie credits for a director."""
        url = f"{TMDB_BASE_URL}/person/{person_id}/movie_credits"
        params = {"language": "en-US"}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_person_details(self, person_id: int) -> Dict:
        """Get person details."""
        url = f"{TMDB_BASE_URL}/person/{person_id}"
        params = {"language": "en-US"}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def discover_movies_by_director(self, person_id: int) -> List[Dict]:
        """Get movies by a specific director."""
        url = f"{TMDB_BASE_URL}/discover/movie"
        params = {
            "with_crew": person_id,
            "without_genres": "99",  # Documentary
            "sort_by": "vote_average.desc",
            "vote_count.gte": 100,
            "language": "en-US"
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json().get("results", [])[:10]


class GPT4MiniClient:
    """Client for OpenAI GPT-4o mini to generate style profiles."""
    
    SYSTEM_PROMPT = """You are a film historian and cinematographer expert. 
Generate detailed cinematic style profiles for directors based on their filmography.
Return ONLY valid JSON matching the specified schema."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def generate_style_profile(self, director_name: str, films: List[Dict]) -> Optional[Dict]:
        """Generate style profile using GPT-4o mini."""
        if not films:
            return None
        
        film_titles = [f.get("title", "Unknown") for f in films[:10]]
        film_list = ", ".join(film_titles)
        
        user_prompt = f"""Analyze the cinematic style of {director_name} based on these films:
{film_list}

For each film, we have:
{json.dumps(films[:5], indent=2)}

Generate a comprehensive style profile with:
1. color_palette: Array of 4-6 hex color codes representing their visual style
2. camera_style: Description of their camera movement and framing
3. lighting_style: Description of their lighting approach
4. editing_style: Description of their editing rhythm and techniques
5. sound_style: Description of their sound/music approach
6. visual_signature: One sentence describing their unique visual fingerprint
7. moods: Array of 5-8 moods associated with their work (e.g., ["Dark", "Cinematic", "Nostalgic"])
8. genres: Array of genres they typically work in
9. popularity_score: Float 0-10 based on influence and acclaim

Return as JSON."""
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30
            )
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"]
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"GPT-4o mini error for {director_name}: {e}")
            return None


# Default style profiles for fallback
DEFAULT_PROFILES = {
    "Christopher Nolan": {
        "color_palette": ["#1A2A4A", "#4A4A4A", "#0A0A0A", "#FF6B00"],
        "camera_style": "IMAX 70mm, wide shots, steady-cam, practical effects",
        "lighting_style": "Natural light, dark shadows, low-key",
        "editing_style": "Slow builds, cross-cutting, non-linear narrative",
        "sound_style": "Hans Zimmer-style, powerful bass, ticking clocks",
        "visual_signature": "Cerebral, mind-bending epics with practical effects",
        "moods": ["Dark", "Epic", "Cerebral", "Suspenseful", "Nostalgic", "Futuristic", "Mind-bending", "Intense"],
        "genres": ["Sci-Fi", "Thriller", "Action", "Drama"]
    },
    "Wes Anderson": {
        "color_palette": ["#FFB6C1", "#FFD700", "#4169E1", "#DC143C"],
        "camera_style": "Symmetrical framing, tracking shots, dollies",
        "lighting_style": "Soft, natural, warm, golden hour",
        "editing_style": "Slow, deliberate, stylised, deadpan",
        "sound_style": "Classic film score, dialogue-focused",
        "visual_signature": "Whimsical, symmetrical compositions with pastel colors",
        "moods": ["Whimsical", "Nostalgic", "Quirky", "Deadpan", "Warm", "Stylised", "Playful", "Sentimental"],
        "genres": ["Comedy", "Drama", "Romance", "Indie"]
    },
    "Hype Williams": {
        "color_palette": ["#FF1493", "#00BFFF", "#FFD700", "#0A0A0A"],
        "camera_style": "Ultra-wide fisheye, low-angle, dynamic movement",
        "lighting_style": "High-contrast, neon saturation, colored gels",
        "editing_style": "Split-screen, fast cuts, slow-motion, animated text overlays",
        "sound_style": "Heavy bass, sub-bass emphasis, punchy kicks",
        "visual_signature": "Larger-than-life, neon-drenched music video aesthetics",
        "moods": ["Neon", "Energetic", "Larger-than-life", "Surreal", "Extravagant", "Bold", "Dynamic", "High-energy"],
        "genres": ["Music Videos", "Hip-Hop", "R&B", "Action"]
    },
    "Quentin Tarantino": {
        "color_palette": ["#FF0000", "#FFD700", "#8B4513", "#0A0A0A"],
        "camera_style": "Trunk shots, close-ups, long takes, 360 pans",
        "lighting_style": "Warm, retro, high-contrast",
        "editing_style": "Sharp cuts, slow-motion, jump cuts",
        "sound_style": "70s funk, surf rock, heavy dialogue",
        "visual_signature": "Stylized violence meets retro pop culture",
        "moods": ["Stylised", "Violent", "Nostalgic", "Dialogue-heavy", "Gritty", "Darkly humorous", "Tense", "Cult"],
        "genres": ["Crime", "Action", "Drama", "Thriller"]
    },
    "Greta Gerwig": {
        "color_palette": ["#FF69B4", "#87CEEB", "#FFF8DC", "#FFD700"],
        "camera_style": "Close-ups, natural framing, character-focused",
        "lighting_style": "Warm, natural, soft, diffused",
        "editing_style": "Smooth, emotional, vibrant, intimate",
        "sound_style": "Emotional piano, strings, intimate",
        "visual_signature": "Warm, feminine, character-driven storytelling",
        "moods": ["Warm", "Authentic", "Feminine", "Vibrant", "Whimsical", "Emotional", "Heartfelt", "Nostalgic"],
        "genres": ["Drama", "Comedy", "Romance", "Coming-of-age"]
    },
    "Jordan Peele": {
        "color_palette": ["#8B0000", "#0A0A0A", "#4A4A4A", "#FFFFFF"],
        "camera_style": "Slow reveals, close-ups, suspense, Steadicam",
        "lighting_style": "Dark, dramatic, low-key, shadowy",
        "editing_style": "Tension builds, jump cuts, slow tension",
        "sound_style": "Tension-building sound design, unsettling music",
        "visual_signature": "Social horror with disturbing imagery and social commentary",
        "moods": ["Suspenseful", "Disturbing", "Terrifying", "Dark", "Thought-provoking", "Tense", "Unsettling", "Socially-conscious"],
        "genres": ["Horror", "Thriller", "Social Commentary", "Comedy"]
    }
}


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def get_or_create_director(db: Session, tmdb_id: int, data: Dict) -> Director:
    """Create or update a director."""
    director = db.query(Director).filter(Director.tmdb_id == tmdb_id).first()
    
    if director:
        # Update existing
        for key, value in data.items():
            if hasattr(director, key) and key not in ['id', 'created_at']:
                setattr(director, key, value)
    else:
        # Create new - remove tmdb_id from data if present
        data_copy = {k: v for k, v in data.items() if k != 'tmdb_id'}
        director = Director(tmdb_id=tmdb_id, **data_copy)
        db.add(director)
    
    db.commit()
    db.refresh(director)
    return director


def process_director(
    tmdb_client: TMDbClient,
    gpt_client: Optional[GPT4MiniClient],
    person_data: Dict,
    db: Session,
    use_ai: bool = True
) -> Optional[Director]:
    """Process a single director from TMDB."""
    person_id = person_data.get("id")
    name = person_data.get("name", "Unknown")
    
    logger.info(f"Processing director: {name} (TMDB ID: {person_id})")
    
    # Get movie credits
    credits = tmdb_client.get_movie_credits(person_id)
    movies = credits.get("crew", [])
    
    # Filter to director roles only
    directed_movies = [m for m in movies if m.get("known_for_department") == "Directing"]
    directed_movies = sorted(directed_movies, key=lambda x: x.get("vote_count", 0), reverse=True)[:10]
    
    if len(directed_movies) < 3:
        logger.info(f"Skipping {name} - not enough directing credits")
        return None
    
    # Get person details
    details = tmdb_client.get_person_details(person_id)
    
    # Prepare director data
    director_data = {
        "name": name,
        "bio": details.get("biography", "")[:2000] if details.get("biography") else None,
        "country": details.get("place_of_birth", "").split(",")[-1].strip() if details.get("place_of_birth") else None,
        "birth_year": int(details.get("birthday", "1900")[:4]) if details.get("birthday") else None,
        "death_year": int(details.get("deathday", "1900")[:4]) if details.get("deathday") else None,
        "image_url": f"{TMDB_IMAGE_BASE}{details.get('profile_path')}" if details.get("profile_path") else None,
        "tmdb_url": f"https://www.themoviedb.org/person/{person_id}",
        "film_count": len(directed_movies),
        "popularity_score": person_data.get("popularity", 0) / 10,
        "is_featured": name in DEFAULT_PROFILES
    }
    
    # Try to get AI-generated profile
    style_profile = None
    if use_ai and gpt_client:
        style_profile = gpt_client.generate_style_profile(name, directed_movies)
        time.sleep(0.5)  # Rate limit
    
    # Use AI profile or fallback to default
    if style_profile:
        director_data.update(style_profile)
    elif name in DEFAULT_PROFILES:
        director_data.update(DEFAULT_PROFILES[name])
    else:
        # Generate basic profile from movies
        genres = list(set([g for m in directed_movies[:5] for g in m.get("genre_ids", [])]))
        director_data.update({
            "color_palette": ["#333333", "#666666", "#999999", "#0A0A0A"],
            "camera_style": "Varied, adaptive to content",
            "lighting_style": "Professional studio lighting",
            "editing_style": "Modern editing techniques",
            "sound_style": "Contemporary sound design",
            "visual_signature": f"Known for {len(directed_movies)} films",
            "moods": ["Cinematic", "Engaging", "Professional"],
            "genres": ["Drama"]  # Default
        })
    
    return get_or_create_director(db, person_id, director_data)


def seed_directors(
    db: Session,
    tmdb_client: TMDbClient,
    gpt_client: Optional[GPT4MiniClient],
    max_directors: int = 100,
    use_ai: bool = True
) -> int:
    """Seed directors from TMDB."""
    logger.info(f"Starting to seed directors (max: {max_directors})")
    
    page = 1
    processed = 0
    errors = 0
    
    while processed < max_directors:
        try:
            response = tmdb_client.get_popular_directors(page=page)
            results = response.get("results", [])
            
            if not results:
                break
            
            for person in results:
                if processed >= max_directors:
                    break
                
                if person.get("known_for_department") != "Directing":
                    continue
                
                try:
                    director = process_director(tmdb_client, gpt_client, person, db, use_ai)
                    if director:
                        processed += 1
                        logger.info(f"Processed: {director.name} ({processed}/{max_directors})")
                except Exception as e:
                    errors += 1
                    logger.error(f"Error processing {person.get('name')}: {e}")
                    time.sleep(1)
            
            page += 1
            time.sleep(0.5)  # Rate limit
            
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            break
    
    logger.info(f"Seeding complete. Processed: {processed}, Errors: {errors}")
    return processed


def add_default_directors(db: Session) -> int:
    """Add default iconic directors with pre-defined profiles."""
    default_directors = [
        {
            "tmdb_id": 525,
            "name": "Christopher Nolan",
            "bio": "British-American film director, producer, and screenwriter. Known for his Hollywood blockbusters with complex storytelling.",
            "country": "United Kingdom",
            "birth_year": 1970,
            "image_url": "https://image.tmdb.org/t/p/w500/7NBX3KLiV3i6X21b8bjFs1h7qTg.jpg",
            "tmdb_url": "https://www.themoviedb.org/person/525-christopher-nolan",
            "film_count": 15,
            "popularity_score": 9.5,
            "is_featured": True
        },
        {
            "tmdb_id": 5655,
            "name": "Wes Anderson",
            "bio": "American filmmaker known for his formal style, deadpan dialogue, and quirky characters.",
            "country": "United States",
            "birth_year": 1969,
            "image_url": "https://image.tmdb.org/t/p/w500/gHtd1yi4gSf1J4XPfImzgBNzV3Z.jpg",
            "tmdb_url": "https://www.themoviedb.org/person/5655-wes-anderson",
            "film_count": 15,
            "popularity_score": 8.8,
            "is_featured": True
        },
        {
            "tmdb_id": 1649,
            "name": "Quentin Tarantino",
            "bio": "American filmmaker known for stylized violence, extended dialogue, and nonlinear storylines.",
            "country": "United States",
            "birth_year": 1963,
            "image_url": "https://image.tmdb.org/t/p/w500/1g8lPiHpvm2hcFOG7xJ3bNBzhMv.jpg",
            "tmdb_url": "https://www.themoviedb.org/person/1649-quentin-tarantino",
            "film_count": 15,
            "popularity_score": 9.2,
            "is_featured": True
        },
        {
            "tmdb_id": 976,
            "name": "Jordan Peele",
            "bio": "American actor, comedian, and filmmaker. Known for blending horror with social commentary.",
            "country": "United States",
            "birth_year": 1979,
            "image_url": "https://image.tmdb.org/t/p/w500/fmepBok9BqJAsY4PGFALrrUzEFE.jpg",
            "tmdb_url": "https://www.themoviedb.org/person/976-jordan-peele",
            "film_count": 10,
            "popularity_score": 8.5,
            "is_featured": True
        },
        {
            "tmdb_id": 2311,
            "name": "Greta Gerwig",
            "bio": "American actress and filmmaker known for her coming-of-age stories and feminist themes.",
            "country": "United States",
            "birth_year": 1983,
            "image_url": "https://image.tmdb.org/t/p/w500/d34aWCXhbQE6AEGdL5XclBHb3rk.jpg",
            "tmdb_url": "https://www.themoviedb.org/person/2311-greta-gerwig",
            "film_count": 10,
            "popularity_score": 8.0,
            "is_featured": True
        },
        {
            "tmdb_id": 57501,
            "name": "Hype Williams",
            "bio": "American music video director known for innovative visual style with fisheye lens and neon aesthetics.",
            "country": "United States",
            "birth_year": 1971,
            "image_url": "https://image.tmdb.org/t/p/w500/8Q2ULxXYJg5QW2HjtBxKPMfMuAF.jpg",
            "tmdb_url": "https://www.themoviedb.org/person/57501-hype-williams",
            "film_count": 200,
            "popularity_score": 7.5,
            "is_featured": True
        }
    ]
    
    count = 0
    for director_data in default_directors:
        name = director_data["name"]
        if name in DEFAULT_PROFILES:
            director_data.update(DEFAULT_PROFILES[name])
        
        director = get_or_create_director(db, director_data["tmdb_id"], director_data)
        if director:
            count += 1
            logger.info(f"Added/updated: {director.name}")
    
    return count


def generate_additional_directors(db: Session) -> List[Dict]:
    """Generate additional director profiles without TMDB (for variety)."""
    additional = [
        {"name": "Steven Spielberg", "country": "United States", "birth_year": 1946, "film_count": 50, "genres": ["Action", "Adventure", "Sci-Fi"], "moods": ["Epic", "Nostalgic", "Suspenseful"], "color_palette": ["#FFD700", "#4169E1", "#0A0A0A", "#DC143C"]},
        {"name": "Martin Scorsese", "country": "United States", "birth_year": 1942, "film_count": 40, "genres": ["Crime", "Drama", "Thriller"], "moods": ["Gritty", "Dark", "Intense"], "color_palette": ["#1A1A1A", "#8B0000", "#DAA520", "#0A0A0A"]},
        {"name": "Alfred Hitchcock", "country": "United Kingdom", "birth_year": 1899, "death_year": 1980, "film_count": 50, "genres": ["Thriller", "Horror", "Mystery"], "moods": ["Suspenseful", "Dark", "Tense"], "color_palette": ["#000000", "#4A4A4A", "#FFFFFF", "#8B0000"]},
        {"name": "Akira Kurosawa", "country": "Japan", "birth_year": 1910, "death_year": 1998, "film_count": 30, "genres": ["Drama", "Action", "Epic"], "moods": ["Epic", "Stylized", "Philosophical"], "color_palette": ["#2F4F4F", "#8B4513", "#FFD700", "#1A1A1A"]},
        {"name": "Stanley Kubrick", "country": "United States", "birth_year": 1928, "death_year": 1999, "film_count": 16, "genres": ["Sci-Fi", "Horror", "Drama"], "moods": ["Dark", "Cerebral", "Disturbing"], "color_palette": ["#0A0A0A", "#FFFFFF", "#1A2A4A", "#8B0000"]},
        {"name": "David Fincher", "country": "United States", "birth_year": 1962, "film_count": 20, "genres": ["Thriller", "Crime", "Drama"], "moods": ["Dark", "Stylized", "Tense"], "color_palette": ["#1A1A1A", "#4A4A4A", "#FFD700", "#0A0A0A"]},
        {"name": "Ridley Scott", "country": "United Kingdom", "birth_year": 1937, "film_count": 30, "genres": ["Sci-Fi", "Action", "Thriller"], "moods": ["Epic", "Dark", "Cinematic"], "color_palette": ["#0A0A0A", "#4A4A4A", "#FF6B00", "#1A2A4A"]},
        {"name": "Tim Burton", "country": "United States", "birth_year": 1958, "film_count": 25, "genres": ["Fantasy", "Horror", "Comedy"], "moods": ["Gothic", "Whimsical", "Dark"], "color_palette": ["#0A0A0A", "#8B0000", "#FFD700", "#9ACD32"]},
        {"name": "Denis Villeneuve", "country": "Canada", "birth_year": 1967, "film_count": 15, "genres": ["Sci-Fi", "Thriller", "Drama"], "moods": ["Epic", "Dark", "Cerebral"], "color_palette": ["#1A2A4A", "#0A0A0A", "#4A4A4A", "#FF6B00"]},
        {"name": "Greta Gerwig", "country": "United States", "birth_year": 1983, "film_count": 10, "genres": ["Drama", "Comedy", "Romance"], "moods": ["Warm", "Authentic", "Nostalgic"], "color_palette": ["#FF69B4", "#87CEEB", "#FFF8DC", "#FFD700"]},
        {"name": "Chloé Zhao", "country": "China", "birth_year": 1982, "film_count": 10, "genres": ["Drama", "Western", "Superhero"], "moods": ["Realistic", "Emotional", "Intimate"], "color_palette": ["#D2691E", "#87CEEB", "#556B2F", "#F5DEB3"]},
        {"name": "Ari Aster", "country": "United States", "birth_year": 1986, "film_count": 8, "genres": ["Horror", "Drama", "Thriller"], "moods": ["Disturbing", "Tense", "Dark"], "color_palette": ["#0A0A0A", "#8B0000", "#4A4A4A", "#FFFFFF"]},
        {"name": "A24 Directors", "country": "United States", "birth_year": 1985, "film_count": 15, "genres": ["Drama", "Horror", "Thriller"], "moods": ["Indie", "Stylized", "Emotional"], "color_palette": ["#1A1A1A", "#4A4A4A", "#D2691E", "#556B2F"]},
        {"name": "Barry Jenkins", "country": "United States", "birth_year": 1979, "film_count": 8, "genres": ["Drama", "Romance", "Musical"], "moods": ["Emotional", "Beautiful", "Nostalgic"], "color_palette": ["#1A1A1A", "#4169E1", "#FFD700", "#FF69B4"]},
        {"name": "Spike Lee", "country": "United States", "birth_year": 1957, "film_count": 40, "genres": ["Drama", "Comedy", "Documentary"], "moods": ["Provocative", "Social", "Energetic"], "color_palette": ["#0A0A0A", "#FF0000", "#FFD700", "#FFFFFF"]},
        {"name": "Denis Villeneuve", "country": "Canada", "birth_year": 1967, "film_count": 15, "genres": ["Sci-Fi", "Thriller", "Drama"], "moods": ["Epic", "Dark", "Cerebral"], "color_palette": ["#1A2A4A", "#0A0A0A", "#4A4A4A", "#FF6B00"]},
        {"name": "Guillermo del Toro", "country": "Mexico", "birth_year": 1964, "film_count": 20, "genres": ["Fantasy", "Horror", "Sci-Fi"], "moods": ["Gothic", "Dark", "Beautiful"], "color_palette": ["#0A0A0A", "#8B0000", "#4A4A4A", "#DAA520"]},
        {"name": "Alfonso Cuarón", "country": "Mexico", "birth_year": 1961, "film_count": 15, "genres": ["Drama", "Sci-Fi", "Romance"], "moods": ["Epic", "Emotional", "Visceral"], "color_palette": ["#1A1A1A", "#4169E1", "#FFD700", "#8B4513"]},
        {"name": "Pedro Almodóvar", "country": "Spain", "birth_year": 1949, "film_count": 25, "genres": ["Drama", "Romance", "Thriller"], "moods": ["Vibrant", "Passionate", "Stylized"], "color_palette": ["#FF1493", "#FFD700", "#FF0000", "#0A0A0A"]},
        {"name": " Bong Joon-ho", "country": "South Korea", "birth_year": 1969, "film_count": 12, "genres": ["Thriller", "Drama", "Comedy"], "moods": ["Dark", "Satirical", "Tense"], "color_palette": ["#0A0A0A", "#4A4A4A", "#FF0000", "#FFFFFF"]},
    ]
    return additional


def seed_additional_directors(db: Session) -> int:
    """Seed additional iconic directors."""
    additional = generate_additional_directors(db)
    count = 0
    
    for i, director_data in enumerate(additional):
        # Check if already exists by name
        existing = db.query(Director).filter(Director.name == director_data["name"]).first()
        if existing:
            continue
        
        # Generate unique tmdb_id using a fixed offset to avoid conflicts
        tmdb_id = 900000 + i  # Use high numbers to avoid TMDB ID conflicts
        
        # Add full profile
        director_data["popularity_score"] = 7.0 + (i / len(additional)) * 2.5
        director_data["is_featured"] = i < 6
        
        # Ensure all fields
        director_data.setdefault("color_palette", ["#333333", "#666666", "#999999", "#0A0A0A"])
        director_data.setdefault("camera_style", "Professional cinematography")
        director_data.setdefault("lighting_style", "Studio lighting")
        director_data.setdefault("editing_style", "Modern editing")
        director_data.setdefault("sound_style", "Professional sound design")
        director_data.setdefault("visual_signature", f"Known for {director_data['film_count']} films")
        director_data.setdefault("moods", ["Cinematic", "Professional"])
        director_data.setdefault("bio", f"Notable {director_data['country']} director known for {director_data['film_count']} films")
        
        # Create director
        director = Director(
            tmdb_id=tmdb_id,
            name=director_data["name"],
            country=director_data.get("country"),
            birth_year=director_data.get("birth_year"),
            death_year=director_data.get("death_year"),
            color_palette=director_data.get("color_palette"),
            camera_style=director_data.get("camera_style"),
            lighting_style=director_data.get("lighting_style"),
            editing_style=director_data.get("editing_style"),
            sound_style=director_data.get("sound_style"),
            visual_signature=director_data.get("visual_signature"),
            moods=director_data.get("moods"),
            genres=director_data.get("genres"),
            popularity_score=director_data["popularity_score"],
            is_featured=director_data["is_featured"],
            film_count=director_data.get("film_count"),
            bio=director_data.get("bio")
        )
        db.add(director)
        count += 1
    
    db.commit()
    logger.info(f"Added {count} additional directors")
    return count


def main():
    parser = argparse.ArgumentParser(description="Seed directors database")
    parser.add_argument("--full", action="store_true", help="Fetch all directors from TMDB")
    parser.add_argument("--incremental", action="store_true", help="Add new directors only")
    parser.add_argument("--featured", action="store_true", help="Just update featured directors")
    parser.add_argument("--max", type=int, default=100, help="Max directors to fetch")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI-generated profiles")
    args = parser.parse_args()
    
    db = get_db()
    
    try:
        if args.featured:
            # Just add default and featured directors
            count1 = add_default_directors(db)
            count2 = seed_additional_directors(db)
            logger.info(f"Added {count1 + count2} featured directors")
        
        elif args.full or args.incremental:
            # Initialize clients
            tmdb_client = TMDbClient(settings.TMDB_API_KEY)
            gpt_client = GPT4MiniClient(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY and not args.no_ai else None
            
            if not settings.TMDB_API_KEY:
                logger.warning("TMDB_API_KEY not set. Adding default directors only.")
                count1 = add_default_directors(db)
                count2 = seed_additional_directors(db)
                logger.info(f"Added {count1 + count2} directors (no TMDB)")
            else:
                # Add defaults first
                add_default_directors(db)
                
                # Seed from TMDB
                processed = seed_directors(
                    db, tmdb_client, gpt_client,
                    max_directors=args.max,
                    use_ai=not args.no_ai
                )
                logger.info(f"Processed {processed} directors from TMDB")
        
        else:
            # Default: add featured + additional
            count1 = add_default_directors(db)
            count2 = seed_additional_directors(db)
            logger.info(f"Added {count1 + count2} directors (default mode)")
        
        # Print stats
        total = db.query(Director).count()
        featured = db.query(Director).filter(Director.is_featured == True).count()
        logger.info(f"Total directors in DB: {total} (featured: {featured})")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
