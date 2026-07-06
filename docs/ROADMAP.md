# Roadmap

## Sprint 1: Infrastructure Foundation

Goal: establish a working development environment that can be started with one command.

Status: Mostly completed

Deliverables:

- Docker Compose stack.
- FastAPI health endpoint.
- Next.js frontend shell.
- Caddy reverse proxy.
- Project documentation foundation.
- Reverse proxy architecture aligned between development and production.

## Future Sprints

Future sprint scope has not been approved yet.

Planned areas, pending explicit task approval:

- Authentication.
- User and organization model.
- Immigration case data model.
- Document storage.
- AI agent workflows.
- Email integrations.

## Sprint 1: Gmail Connectivity

Goal: connect a real Gmail account with OAuth2 and receive new email notifications through Gmail Watch API.

Status: In progress

Deliverables:

- Gmail OAuth2 connect and callback endpoints.
- Encrypted Gmail refresh token storage.
- Gmail account and watch tables in PostgreSQL.
- Gmail settings frontend for connect and status visibility.
- Google Cloud OAuth and Pub/Sub environment setup for local validation.
