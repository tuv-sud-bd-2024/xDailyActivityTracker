# xDailyActivityTracker - Backend

This folder contains a FastAPI backend scaffold for the xDailyActivityTracker project.

Quick start (dev):

1. Create a virtualenv and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2. Run the app:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Notes:
- Default DB is `sqlite:///./dev.db`. Set `DATABASE_URL` env var for Postgres in production.
- Gemini Flash client is a stub; set `GEMINI_API_KEY` and implement the client in `backend/app/llm_client.py` when ready.
