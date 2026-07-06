# Setup

## Requirements

- Docker
- Docker Compose v2

## Start Local Development

From the project root:

```bash
docker compose up -d
```

## Verify Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Stop Local Development

```bash
docker compose down
```

## Rebuild Backend

```bash
docker compose build backend
```

## Local URLs

| Service | URL |
| --- | --- |
| Frontend through Caddy | `http://localhost` |
| Backend health endpoint | `http://localhost:8000/health` |

