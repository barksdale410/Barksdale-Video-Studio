# Contributing to Barksdale Video Studio

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

- **Bug Reports**: Report bugs via GitHub Issues
- **Feature Requests**: Suggest new features
- **Code Contributions**: Submit PRs for bug fixes or features
- **Documentation**: Improve docs, tutorials, or examples
- **Director Data**: Help add or verify director profiles

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/barksdale-video-studio.git
   cd barksdale-video-studio
   ```

3. Set up environment:
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your API keys
   ```

4. Start services:
   ```bash
   docker-compose up -d
   # Or for manual setup:
   # See README.md for instructions
   ```

5. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Coding Standards

### Python (Backend)

- Follow PEP 8
- Use type hints where possible
- Add docstrings for public functions
- Keep functions small and focused
- Write unit tests for new functionality

```python
# Example
def analyze_script(script: str, director_id: int) -> dict:
    """
    Analyze a script and return storyboard scenes.
    
    Args:
        script: The script text to analyze
        director_id: ID of the director for style
        
    Returns:
        Dict containing scenes and metadata
    """
    pass
```

### JavaScript/React (Frontend)

- Use functional components with hooks
- Follow existing naming conventions
- Use Tailwind CSS for styling
- Write tests for new components

```jsx
// Example
function DirectorCard({ director, onSelect }) {
  return (
    <div className="card" onClick={() => onSelect(director)}>
      {/* ... */}
    </div>
  )
}
```

## 🔄 Pull Request Process

### PR Checklist

Before submitting a PR, ensure:

- [ ] Code follows the project's style guidelines
- [ ] Tests pass locally
- [ ] New code has unit tests
- [ ] Documentation is updated (if needed)
- [ ] No console.log or debug statements
- [ ] Commit messages are clear and descriptive

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes

## Screenshots (if applicable)
Add screenshots for UI changes
```

## 🐛 Bug Reports

Use GitHub Issues with this template:

```markdown
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen

**Screenshots**
If applicable, add screenshots

**Environment**
- OS: [e.g., macOS, Windows, Linux]
- Browser: [e.g., Chrome, Safari]
- Version: [e.g., 1.0.0]
```

## 🎨 Adding New Directors

To add a new director to the database:

1. Add to `scripts/seed_directors.py`:
   ```python
   {
       "name": "Director Name",
       "country": "Country",
       "birth_year": 1970,
       # ... other fields
   }
   ```

2. Run the seed script:
   ```bash
   python scripts/seed_directors.py --featured
   ```

3. Or use the API:
   ```bash
   curl -X POST /api/v1/directors \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"name": "...", ...}'
   ```

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Questions?

Feel free to:
- Open an issue for questions
- Join our discussions
- Email the maintainers

Thank you for contributing! 🎬
