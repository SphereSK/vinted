# Database Migrations

This directory contains SQL migration scripts for database schema changes.

## Running Migrations

### PostgreSQL

```bash
# Set your database URL
export DATABASE_URL="postgresql+asyncpg://vinted_user:password@127.0.0.1:6432/vinted_db"

# Run migration (extract connection details and use psql)
psql -h 127.0.0.1 -p 6432 -U vinted_user -d vinted_db -f migrations/001_add_source_column.sql
```

### SQLite

```bash
# For SQLite, uncomment the SQLite-specific lines in the migration file first
sqlite3 vinted.db < migrations/001_add_source_column.sql
```

## Migration History

| #   | File                           | Description                                  | Date       |
| --- | ------------------------------ | -------------------------------------------- | ---------- |
| 001 | `001_add_source_column.sql`    | Add source field to track marketplace origin | 2025-10-14 |

## Creating New Migrations

1. Create a new file with format: `NNN_description.sql`
2. Add both PostgreSQL and SQLite versions (with comments)
3. Include rollback instructions if applicable
4. Update this README with migration details
