# Database Migrations Guide

The Agent Platform uses **Alembic** for database schema migrations.

## Workflow

### 1. Create a Migration
When you modify models in `database/models.py`, generate a new migration script:

```bash
make migration MSG="description of changes"
```
*Note: This uses Alembic's `--autogenerate` feature. Always inspect the generated file in `database/migrations/versions/` for correctness.*

### 2. Apply Migrations
Apply all pending migrations to the database:

```bash
make migrate
```

### 3. Check State
To see the current revision and history:

```bash
make db-current
make db-history
```

## Configuration

Migrations are configured in `alembic.ini` and `database/migrations/env.py`.
The `env.py` has been fixed to:
- Use `sqlalchemy.ext.asyncio` for compatibility with the app's async engine.
- Pull the `DATABASE_URL` dynamically from the `Settings` class in `core.config`.
- Propagate errors correctly instead of failing silently.

## Troubleshooting

- **"sqlalchemy.exc.NoSuchModuleError"**: Ensure you have `asyncpg` installed and the URL starts with `postgresql+asyncpg://`.
- **"Target database is not up to date"**: Run `make migrate` to apply pending revisions.
- **Empty migrations**: If `--autogenerate` produces an empty `upgrade()` function, ensure your new model is imported in `database/models.py` and that `Base` is used correctly.
