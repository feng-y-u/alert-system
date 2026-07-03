# AGENTS.md

## Project Overview

Campus account anomaly detection & alert platform (academic project). Backend-only currently — frontend not yet scaffolded.

## Key Files

- `backend/app/main.py` — FastAPI entrypoint, registers routers
- `backend/app/api/` — API routes (one file per feature)
- `backend/requirements.txt` — Python dependencies (currently only fastapi + uvicorn)
- `.harness/rules/rules.md` — Mandatory task workflow rules
- `.harness/changes/` — Every task MUST create a dated folder here with `task.md`
- `docs/DESIGN.md` — Full design spec (data models, weekly plan, code patterns)

## Must-Do for Every Task

1. Create `.harness/changes/YYYY-MM-DD-task-name/task.md` before coding
2. Define task goal + acceptance criteria in that file
3. After completion, fill in actual verification results in the same file
4. Follow modular pattern: new feature = new file in `app/api/`, then register in `main.py`

## Constraints

- **Database**: MySQL only (not PostgreSQL)
- **Auth**: JWT tokens, role-based (user/admin)
- **Async**: Celery + Redis for email/detection tasks
- **Style**: Black for Python, match existing code patterns exactly
- **No comments** in code unless explicitly requested

## Dev Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API docs at http://localhost:8000/docs
```

## Adding a New API Module

1. Create `backend/app/api/<feature>.py` with `router = APIRouter()`
2. Import and register in `main.py`: `app.include_router(feature_router, prefix="/api", tags=["标签"])`

## Gotchas

- `.harness/` directory structure is read-only — never modify it
- All console output must follow project format (see rules.md)
- Document alongside code — put docs in the same changes folder
