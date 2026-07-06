# Changelog

All notable project changes are tracked here.

## Unreleased

### Added

- Project documentation source of truth in `docs/`.

## 2026-07-06

### Added

- Initial Docker Compose infrastructure.
- FastAPI backend with `GET /health`.
- Next.js frontend shell.
- Caddy reverse proxy.
- PostgreSQL 16, Redis 7, and Qdrant services.

### Fixed

- Replaced backend Docker dependency installation strategy so `fastapi` and `uvicorn` are available at runtime.

