## Caravanes FastAPI

### Quickstart

1. Create and activate a virtualenv
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create a .env file with your configuration
```bash
# Database
DATABASE_URL=sqlite:///./caravanes.db

# Gemini API (required for OCR functionality)
GEMINI_API_KEY=your_gemini_api_key_here

# App Configuration
APP_NAME=Caravanes API
ENVIRONMENT=development
DEBUG=true
```

4. Run the API
```bash
uvicorn app.main:app --reload
```

### API Endpoints

- `GET /health`: Health check endpoint
- `POST /ocr/extract`: Extract data from Arabic license card images using Google Gemini Vision API

### Structure
- `app/main.py`: application factory and middleware
- `app/api/`: API routers (`health`, `ocr`)
- `app/core/`: settings and configuration
- `app/db/`: SQLAlchemy engine/session/base
- `app/models/`: SQLAlchemy models
- `app/schema/`: Pydantic schemas
- `app/crud/`: CRUD helpers

### OCR Functionality

The OCR endpoint uses Google Gemini Vision API to extract:
- License number
- First name
- Last name

From Arabic license card images. Make sure to set your `GEMINI_API_KEY` in the `.env` file.
