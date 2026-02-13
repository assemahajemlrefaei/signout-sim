# signout-sim

AI-augmented signout simulation and training platform for residents, using structured I-PASS handoff, night-cover simulation, rubric-based evaluation, and deliberate practice.

## Scaffolded local development setup

This repository includes:

- `frontend/`: Next.js app with a basic homepage.
- `backend/`: FastAPI app with a typed `/health` endpoint.
- `infra/docker-compose.yml`: local orchestration for frontend, backend, and Postgres.

## Run locally with Docker Compose

From the repository root:

```bash
cd infra
docker compose up --build
```

Services:

- Frontend: <http://localhost:3000>
- Backend health: <http://localhost:8000/health>
- Postgres: `localhost:5432`

Stop services:

```bash
docker compose down
```

## Run backend tests locally

From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```
