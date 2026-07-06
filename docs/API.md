# API

## Base URLs

Local backend:

```text
http://localhost:8000
```

Through Caddy:

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

## API Change Policy

Any endpoint, request shape, response shape, status code, or authentication requirement change must update this document in the same task.

