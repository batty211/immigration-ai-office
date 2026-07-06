# API

## Base URLs

Public entry point through Caddy:

```text
http://localhost
```

## Endpoints

### GET /health

Returns backend service health.

Request:

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

Status code:

```text
200 OK
```

### GET /gmail/connect

Starts Google OAuth2 for a personal Gmail account and redirects the browser to Google.

Response:

```text
302 Found
```

### GET /gmail/callback

Receives the Google OAuth2 callback, stores the encrypted Gmail refresh token, and redirects back to the frontend settings page.

Response:

```text
302 Found
```

### POST /gmail/watch

Registers Gmail Watch API push notifications for the connected Gmail account.

Request:

```http
POST /gmail/watch
```

Successful response:

```json
{
  "connected": true,
  "history_id": "123456",
  "expiration": "2026-07-13T10:15:30+00:00",
  "stored": 12,
  "processed": 12
}
```

### POST /gmail/sync

Fetches recent Gmail messages immediately, stores them in PostgreSQL, and marks them processed for dashboard display.

Request:

```http
POST /gmail/sync
```

Successful response:

```json
{
  "connected": true,
  "history_id": "123456",
  "stored": 3,
  "processed": 25
}
```

### POST /gmail/notifications

Receives Gmail Pub/Sub push notifications, syncs newly added messages from Gmail history, stores them, and marks them processed.

Request:

```http
POST /gmail/notifications
Content-Type: application/json
```

Successful response:

```json
{
  "ok": true,
  "email": "user@gmail.com",
  "history_id": "123789",
  "stored": 1,
  "processed": 1
}
```

### GET /gmail/dashboard

Returns the stored email records and any available Mail Officer analysis that power the dashboard.

Request:

```http
GET /gmail/dashboard
```

Successful response when connected:

```json
{
  "connected": true,
  "email": "user@gmail.com",
  "last_sync": "2026-07-06T08:30:00+00:00",
  "metrics": {
    "stored": 25,
    "processed": 25,
    "unread": 7
  },
  "messages": [
    {
      "id": 42,
      "gmail_message_id": "19779f9f2f2b4abc",
      "subject": "Case update",
      "sender": "client@example.com",
      "recipients": "office@example.com",
      "snippet": "Please find the latest document attached...",
      "body": "Please find the latest document attached...",
      "received_at": "2026-07-06T08:12:00+00:00",
      "processing_status": "processed",
      "attachments": [],
      "is_unread": true,
      "analysis": {
        "summary": "Document request for an active immigration case.",
        "category": "document_request",
        "priority": "HIGH",
        "requires_action": true,
        "requires_reply": true,
        "deadline": "ภายในวันนี้",
        "recommended_action": "Reply to sender.",
        "recommended_assignee": "Case Officer",
        "tags": ["case", "documents"],
        "confidence": 0.94
      }
    }
  ]
}
```

### POST /emails/{id}/analyze

Runs Mail Officer analysis for one stored email and stores one structured analysis record linked to that email.

Request:

```http
POST /emails/42/analyze
```

Successful response:

```json
{
  "id": 9,
  "email_message_id": 42,
  "summary": "Document request for an active immigration case.",
  "category": "document_request",
  "priority": "HIGH",
  "requires_action": true,
  "requires_reply": true,
  "deadline": "ภายในวันนี้",
  "recommended_action": "Reply to sender.",
  "recommended_assignee": "Case Officer",
  "tags": ["case", "documents"],
  "confidence": 0.94,
  "created_at": "2026-07-06T09:00:00+00:00",
  "updated_at": "2026-07-06T09:00:00+00:00"
}
```

### GET /emails/{id}/analysis

Returns the stored Mail Officer analysis for one email.

Request:

```http
GET /emails/42/analysis
```

### POST /emails/analyze-pending

Batch processes all stored emails that do not yet have an `email_analysis` record.

Request:

```http
POST /emails/analyze-pending
```

Successful response:

```json
{
  "pending": 12,
  "analyzed": 12
}
```

### GET /gmail/status

Returns Gmail connection status for the most recently connected account.

Request:

```http
GET /gmail/status
```

### Proxying Notes

- Browser requests should use Caddy at `http://localhost`.
- Frontend XHR/fetch requests should use `/api/*`, which Caddy forwards to the backend after removing the `/api` prefix.
- Direct browser routes such as `/gmail/connect`, `/gmail/callback`, and `/docs` are also served through Caddy.

Successful response when connected:

```json
{
  "connected": true,
  "email": "user@gmail.com",
  "last_sync": "2026-07-06T08:30:00+00:00",
  "stored_messages": 25
}
```

Successful response when disconnected:

```json
{
  "connected": false,
  "email": null,
  "last_sync": null,
  "stored_messages": 0
}
```

## API Change Policy

Any endpoint, request shape, response shape, status code, or authentication requirement change must update this document in the same task.
