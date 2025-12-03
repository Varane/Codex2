# Sonver Auto Parts Request

A minimal end-to-end sample for requesting auto parts with vehicle autocomplete. Runs with Docker Compose using FastAPI, PostgreSQL, Alembic migrations, and a static frontend.

## Quick start

```bash
docker compose up --build
```

Then open the frontend at [http://localhost:8080](http://localhost:8080).

The backend API runs at [http://localhost:8000](http://localhost:8000) and applies Alembic migrations automatically on startup.
