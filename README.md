# 🎬 BARKSDALE VIDEO STUDIO

AI-powered video storyboard generator that transforms scripts into cinematic visuals.

## Features

- **Script Analysis**: Parse and analyze screenplays
- **Director Styles**: Choose from 6 iconic directors (Hype Williams, Christopher Nolan, Wes Anderson, Quentin Tarantino, Greta Gerwig, Jordan Peele)
- **Genre Selection**: 10 genres including Action, Drama, Sci-Fi, Horror, Comedy
- **Mood Control**: 24 mood options from Dark to Whimsical
- **Storyboard Generation**: AI-powered scene breakdown with director-style visual descriptions
- **Video Generation**: Generate video concepts based on storyboards

## Architecture

- **Backend**: FastAPI (Python) → [Render](https://render.com)
- **Frontend**: HTML/CSS/JS → [GitHub Pages](https://pages.github.com)

## Quick Start

### 1. Deploy Backend on Render
See [deployment.md](./deployment.md) for detailed instructions.

### 2. Enable GitHub Pages
In repository Settings → Pages → Source: `main` / `/frontend`

### 3. Configure & Use
1. Open the frontend app
2. Enter your Render backend URL
3. Select a director, genre, and mood
4. Paste your script
5. Click "Analyze Script"
6. Click "Generate Movie"

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/options` | GET | Get directors, genres, moods |
| `/api/directors` | GET | Get all director details |
| `/api/script/analyze` | POST | Analyze script and generate storyboard |
| `/api/video/generate` | POST | Generate video from storyboard |

## Project Structure

```
barksdale-video-studio/
├── backend/
│   ├── server.py          # FastAPI application
│   └── requirements.txt  # Python dependencies
├── frontend/
│   └── index.html        # Frontend application
├── templates/
│   ├── directors.json    # Director profiles
│   ├── genres.json       # Genre definitions
│   └── mood.json         # Mood options
├── deployment.md         # Deployment guide
└── README.md            # This file
```

## Tech Stack

- **Backend**: FastAPI, Pydantic, Uvicorn
- **Frontend**: Vanilla HTML/CSS/JS
- **Deploy**: Render (backend), GitHub Pages (frontend)

## License

MIT