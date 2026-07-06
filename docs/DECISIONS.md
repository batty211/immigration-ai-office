# Architecture Decision Records

## ADR-001: Use Docker Compose for Local Development

Status: Accepted

Context:

The project needs a one-command development environment.

Decision:

Use Docker Compose to run PostgreSQL, Redis, Qdrant, FastAPI, Next.js, and Caddy.

Consequences:

- Developers can start the environment with `docker compose up -d`.
- Service boundaries are explicit from the beginning.
- Local infrastructure resembles production architecture enough for early development.

## ADR-002: Use FastAPI for Backend

Status: Accepted

Context:

The backend needs a Python API framework suitable for future service and AI integration work.

Decision:

Use FastAPI on Python 3.12.

Consequences:

- REST endpoints can be developed quickly.
- OpenAPI support is available when API surface grows.

## ADR-003: Use Standard Runtime Dependency Installation for Backend Docker Image

Status: Accepted

Context:

Installing Python dependencies with `pip install --prefix=/install` caused runtime import visibility problems.

Decision:

Install backend dependencies directly into the runtime image from `backend/requirements.txt`.

Consequences:

- `fastapi` and `uvicorn` are importable in the final container.
- The Dockerfile is simpler and easier to debug.
- Future optimization can introduce a virtualenv multi-stage build if needed.

