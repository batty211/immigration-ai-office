# Security

## Current State

The project currently contains infrastructure only.

The project includes Gmail OAuth2 for personal Gmail accounts.

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
| `APP_BASE_URL` | Public backend base URL used to build OAuth callback URLs. |
| `FRONTEND_BASE_URL` | Frontend base URL used after Gmail OAuth callback completes. |
| `GOOGLE_CLIENT_ID` | Google OAuth client id for Gmail integration. |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret for Gmail integration. |
| `GMAIL_OAUTH_REDIRECT_PATH` | Gmail OAuth callback path. |
| `GMAIL_TOKEN_ENCRYPTION_KEY` | Fernet key used to encrypt Gmail refresh tokens before storage. |
| `GMAIL_PUBSUB_TOPIC_NAME` | Pub/Sub topic used by Gmail Watch API. |
| `GMAIL_WATCH_LABEL_IDS` | Comma-separated Gmail labels to watch. |

## Gmail Token Handling

- Gmail OAuth requests offline access so the backend can store a refresh token.
- Refresh tokens are encrypted with Fernet before writing to PostgreSQL.
- `https://www.googleapis.com/auth/gmail.readonly` is a restricted Gmail scope and may require Google verification and additional compliance controls before production use.

## Security Change Policy

Any change involving authentication, authorization, secrets, personal data, external integrations, or network exposure must update this document.
