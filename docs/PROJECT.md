# Immigration AI Office Project

## Vision

Immigration AI Office is intended to become a production-grade office platform for immigration workflows, starting with a reliable local development foundation.

## Objectives

- Provide a one-command local development environment.
- Keep documentation synchronized with the source code.
- Build infrastructure before product features.
- Maintain clear boundaries between backend, frontend, data stores, and future AI agents.

## Sprint 1 Scope

Sprint 1 covers infrastructure and the first Gmail connectivity slice needed to validate end-to-end local operation.

Included:

- Docker Compose development environment.
- FastAPI backend with `GET /health`.
- Next.js frontend shell.
- PostgreSQL, Redis, Qdrant, and Caddy services.
- Gmail OAuth2 connect and callback flow.
- Gmail status and watch registration flow.
- Project documentation source of truth.

Not included:

- Authentication.
- AI workflows.
- Business logic.
- Immigration case management features.

## Current Progress

The project now has a working application skeleton running through the intended reverse proxy architecture:

- Browser -> Caddy -> Next.js frontend and FastAPI backend.
- Backend health endpoint is implemented at `GET /health`.
- Frontend dashboard and Gmail settings screens are implemented.
- Gmail OAuth configuration, encrypted token storage, and watch registration endpoints are implemented.

## Current Status

Completed foundations:

- Local Docker Compose stack for frontend, backend, PostgreSQL, Redis, Qdrant, and Caddy.
- Core backend runtime and health endpoint.
- Core frontend shell and backend status visibility.
- Gmail OAuth backend routes and frontend settings page.
- Architecture restored so development and production both use Caddy as the main entry point.

Work still in progress:

- Final environment setup for Google OAuth and Gmail Pub/Sub in `.env`.
- Real end-to-end validation with a Gmail account in local development.
- Continued cleanup of outdated documentation that still refers to older local debug flows.

## Documentation Rules

Documentation is the source of truth for the project.

Every completed task must update:

- `docs/TASKS.md`
- `docs/CHANGELOG.md`
- `docs/API.md` when APIs change
- `docs/DATABASE.md` when schema changes
- `docs/ARCHITECTURE.md` when architecture changes
