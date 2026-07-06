# API

## Base URLs

Local backend:

```text
http://localhost:8001
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
  "expiration": "2026-07-13T10:15:30+00:00"
}
```

### GET /gmail/status

Returns Gmail connection status for the most recently connected account.

Request:

```http
GET /gmail/status
```

Successful response when connected:

```json
{
  "connected": true,
  "email": "user@gmail.com",
  "last_sync": "2026-07-06T08:30:00+00:00"
}
```

Successful response when disconnected:

```json
{
  "connected": false,
  "email": null,
  "last_sync": null
}
```

## API Change Policy

Any endpoint, request shape, response shape, status code, or authentication requirement change must update this document in the same task.
