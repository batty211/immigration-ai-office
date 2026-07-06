# Database

## Current State

The backend creates the Gmail integration tables on startup with SQLAlchemy metadata.

The local development environment includes PostgreSQL 16 with the default database:

| Setting | Value |
| --- | --- |
| Database | `immigration_ai_office` |
| User | `immigration` |
| Host inside Compose | `postgres` |
| Port inside Compose | `5432` |

## Current Relationships

| Table | Purpose |
| --- | --- |
| `gmail_accounts` | Stores connected Gmail accounts and encrypted refresh tokens. |
| `gmail_watch` | Stores Gmail Watch API subscription state for each connected account. |

```mermaid
erDiagram
    gmail_accounts ||--o| gmail_watch : "has active watch"

    gmail_accounts {
        int id PK
        string email_address UK
        text encrypted_refresh_token
        text scopes
        string history_id
        datetime last_sync_at
        datetime connected_at
        datetime created_at
        datetime updated_at
    }

    gmail_watch {
        int id PK
        int gmail_account_id FK
        string history_id
        datetime expiration_at
        string topic_name
        string status
        datetime created_at
        datetime updated_at
    }
```

## Schema Change Policy

Any schema, migration, table, index, enum, or relationship change must update this document in the same task.
