# Immigration AI Office

Development workspace for the Immigration AI Office project, including Gmail OAuth integration, Gmail message ingestion, and a live email dashboard backed by PostgreSQL.

## Installation

1. Install Docker and Docker Compose v2.
2. Copy `.env.example` to `.env` if you want to customize ports or service settings.
3. Start the stack with:

```bash
docker compose up --build -d
```

## Stop the stack

```bash
docker compose down
```

## Services

- PostgreSQL 16
- Redis 7
- Qdrant
- FastAPI backend
- Next.js frontend
- Gmail OAuth2 and Gmail Watch API integration

## Development URLs

- App entry point: `http://localhost`
- Backend health: `http://localhost/health`
- Swagger: `http://localhost/docs`
- Debug frontend: `http://localhost:3001`
- Debug backend: `http://localhost:8001`
