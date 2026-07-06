# Security

## Current State

The project currently contains infrastructure only.

Authentication, authorization, Gmail integration, AI integrations, and business workflows are not implemented.

## Secrets Management

- `.env.example` documents expected environment variables.
- `.env` is ignored by Git and must not be committed.
- Development defaults are for local use only.
- Production secrets must be managed outside the repository.

## Current Environment Variables

| Variable | Purpose |
| --- | --- |
| `POSTGRES_USER` | Local PostgreSQL user. |
| `POSTGRES_PASSWORD` | Local PostgreSQL password. |
| `POSTGRES_DB` | Local PostgreSQL database. |
| `REDIS_URL` | Backend Redis connection URL. |
| `QDRANT_URL` | Backend Qdrant connection URL. |

## Security Change Policy

Any change involving authentication, authorization, secrets, personal data, external integrations, or network exposure must update this document.

