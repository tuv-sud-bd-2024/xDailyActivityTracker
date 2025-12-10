Alembic migrations for xDailyActivityTracker

Usage:

1. Ensure `DATABASE_URL` is set (defaults to `sqlite:///./dev.db`):

```bash
export DATABASE_URL=sqlite:///./dev.db
```

2. Create a new revision (autogenerate):

```bash
alembic -c backend/alembic.ini revision --autogenerate -m "init"
```

3. Apply migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

Note: Run commands from repository root. Alembic env is configured to import `backend.app.models` so ensure project dependencies are installed.
