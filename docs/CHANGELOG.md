# Changelog

All notable project changes are tracked here.

## Unreleased

### Changed

- Local development no longer depends on Caddy; frontend is exposed on `http://localhost:3001` and backend on `http://localhost:8001`.
- Frontend now calls the backend directly in development mode, with CORS enabled for the local UI origin.

### Added

- Project documentation source of truth in `docs/`.
- Gmail OAuth2 integration for personal Gmail accounts.
- Encrypted refresh token storage in PostgreSQL.
- Gmail Watch API registration endpoint and Gmail settings frontend.

## 2026-07-06

### Added

- Initial Docker Compose infrastructure.
- FastAPI backend with `GET /health`.
- Next.js frontend shell.
- Caddy reverse proxy.
- PostgreSQL 16, Redis 7, and Qdrant services.

### Fixed

- Replaced backend Docker dependency installation strategy so `fastapi` and `uvicorn` are available at runtime.
