# Tasks

## Backlog

| ID | Task | Status | Notes |
| --- | --- | --- | --- |
| DOC-001 | Establish project documentation source of truth | Completed | Created required Markdown documentation set. |
| INFRA-001 | Initial Docker Compose infrastructure | Completed | Added PostgreSQL, Redis, Qdrant, backend, frontend, and Caddy. |
| BUGFIX-001 | Fix backend runtime dependency visibility | Completed | Replaced dependency install strategy with a standard backend Dockerfile. |
| FEAT-001 | Gmail OAuth and watch integration foundation | In Progress | Backend routes, frontend settings page, and token storage are implemented; real environment setup is still ongoing. |
| BUGFIX-003 | Restore Caddy reverse proxy architecture | Completed | Reinstated Caddy as the primary entry point and routed frontend/backend traffic through it. |

## Current Rules

- No feature implementation may happen before the relevant documentation is updated.
- Completed tasks must update this file and `docs/CHANGELOG.md`.
- API changes must update `docs/API.md`.
- Database schema changes must update `docs/DATABASE.md`.
- Architecture changes must update `docs/ARCHITECTURE.md`.
