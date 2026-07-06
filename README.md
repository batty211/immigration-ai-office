# Immigration AI Office

Development workspace for the Immigration AI Office project, including Gmail OAuth integration for personal Gmail accounts.

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

- Frontend: `http://localhost:3001`
- Backend: `http://localhost:8001`
- Swagger: `http://localhost:8001/docs`
