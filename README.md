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

3. Create a .env (optional)
```bash
cp .env.example .env
```

4. Run the API
```bash
uvicorn app.main:app --reload
```

### Structure
- `app/main.py`: application factory and middleware
- `app/api/`: API routers (`health`, `users`)
- `app/core/`: settings and configuration
- `app/db/`: SQLAlchemy engine/session/base
- `app/models/`: SQLAlchemy models
- `app/schema/`: Pydantic schemas
- `app/crud/`: CRUD helpers
