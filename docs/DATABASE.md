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
| `email_messages` | Stores real Gmail messages after ingestion and processing for dashboard visibility. |
| `email_analysis` | Stores one Mail Officer analysis record for each analyzed email message. |

```mermaid
erDiagram
    gmail_accounts ||--o| gmail_watch : "has active watch"
    gmail_accounts ||--o{ email_messages : "owns stored messages"
    email_messages ||--o| email_analysis : "has one analysis"

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

    email_messages {
        int id PK
        int gmail_account_id FK
        string gmail_message_id UK
        string gmail_thread_id
        string gmail_history_id
        text subject
        text sender
        text recipients
        text snippet
        text body
        json attachments
        json label_ids
        datetime received_at
        string processing_status
        datetime processed_at
        boolean is_unread
        datetime created_at
        datetime updated_at
    }

    email_analysis {
        int id PK
        int email_message_id FK
        text summary
        string category
        string priority
        boolean requires_action
        boolean requires_reply
        string deadline
        text recommended_action
        text recommended_assignee
        json tags
        float confidence
        json raw_result
        datetime created_at
        datetime updated_at
    }
```

## Schema Change Policy

Any schema, migration, table, index, enum, or relationship change must update this document in the same task.
