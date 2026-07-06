# Immigration AI Office Project

## Vision

Immigration AI Office is intended to become a production-grade office platform for immigration workflows, starting with a reliable local development foundation.

## Objectives

- Provide a one-command local development environment.
- Keep documentation synchronized with the source code.
- Build infrastructure before product features.
- Maintain clear boundaries between backend, frontend, data stores, and future AI agents.

## Sprint 1 Scope

Sprint 1 is infrastructure only.

Included:

- Docker Compose development environment.
- FastAPI backend with `GET /health`.
- Next.js frontend shell.
- PostgreSQL, Redis, Qdrant, and Caddy services.
- Project documentation source of truth.

Not included:

- Authentication.
- Gmail integration.
- AI workflows.
- Business logic.
- Immigration case management features.

## Documentation Rules

Documentation is the source of truth for the project.

Every completed task must update:

- `docs/TASKS.md`
- `docs/CHANGELOG.md`
- `docs/API.md` when APIs change
- `docs/DATABASE.md` when schema changes
- `docs/ARCHITECTURE.md` when architecture changes

