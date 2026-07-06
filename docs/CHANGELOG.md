# Changelog

All notable project changes are tracked here.

## Unreleased

### Changed

- Restored Caddy as the primary entry point for local development so development and production use the same reverse proxy architecture.
- Frontend now calls backend API routes through Caddy using `/api/*` instead of hardcoded backend host URLs.

### Added

- Project documentation source of truth in `docs/`.
- Gmail OAuth2 integration for personal Gmail accounts.
- Encrypted refresh token storage in PostgreSQL.
- Gmail Watch API registration endpoint and Gmail settings frontend.
- Mail Officer service for structured executive email analysis.
- `email_analysis` storage linked one-to-one with `email_messages`.
- Email analysis API endpoints for single-email and batch processing.
- Executive dashboard fields for summary, priority, recommended action, and deadline.

### In Progress

- Google OAuth local environment setup and test-user configuration.
- Gmail Pub/Sub topic setup for watch notifications.

## 2026-07-06

### Added

- Initial Docker Compose infrastructure.
- FastAPI backend with `GET /health`.
- Next.js frontend shell.
- Caddy reverse proxy.
- PostgreSQL 16, Redis 7, and Qdrant services.

### Fixed

- Replaced backend Docker dependency installation strategy so `fastapi` and `uvicorn` are available at runtime.
