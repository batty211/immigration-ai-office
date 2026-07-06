# Setup

## Requirements

- Docker
- Docker Compose v2

## Start Local Development

1. Copy `.env.example` to `.env`.
2. Fill in Google OAuth and Gmail settings before starting the stack:

```text
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
GMAIL_TOKEN_ENCRYPTION_KEY=your-fernet-key
GMAIL_PUBSUB_TOPIC_NAME=projects/your-project-id/topics/your-topic
```

3. Generate `GMAIL_TOKEN_ENCRYPTION_KEY` with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. In Google Cloud Console:

- Enable Gmail API.
- Create an OAuth 2.0 Web application credential.
- Add `http://localhost/gmail/callback` as an authorized redirect URI.
- Create the Pub/Sub topic referenced by `GMAIL_PUBSUB_TOPIC_NAME`.
- Grant Gmail permission to publish to that topic.

5. Start the stack:

From the project root:

```bash
docker compose up -d
```

## Verify Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Stop Local Development

```bash
docker compose down
```

## Rebuild Backend

```bash
docker compose build backend
```

## Local URLs

| Service | URL |
| --- | --- |
| Frontend through Caddy | `http://localhost` |
| Backend health endpoint | `http://localhost:8000/health` |
| Gmail settings page | `http://localhost/gmail-settings` |
