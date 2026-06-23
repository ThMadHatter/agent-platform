# Operations Guide

## Deployment

The Agent Platform is designed to run on a Proxmox LXC container using Docker Compose.

### Steps

1. **Prepare LXC**: Create a Debian/Ubuntu LXC with Docker and Docker Compose installed.
2. **Clone Repo**: `git clone <repo_url>`
3. **Configure**: Create `.env` from `.env.example`.
4. **Deploy**:
   ```bash
   docker-compose up -d
   ```
5. **Migrations**:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

## Backup and Recovery

### Metadata (PostgreSQL)

Perform a daily dump of the PostgreSQL database:
```bash
docker-compose exec db pg_dump -U postgres agent_platform > backup.sql
```

### Documents (Google Drive)

Documents are stored in Google Drive, which provides native versioning and backup.

### Vectors (Qdrant)

Qdrant data is stored in the `qdrant_data` volume. Backup the volume directory for persistent storage.

## Upgrades

1. **Pull Code**: `git pull origin main`
2. **Rebuild Image**:
   ```bash
   docker-compose build api
   ```
3. **Apply Migrations**:
   ```bash
   docker-compose exec api alembic upgrade head
   ```
4. **Restart**:
   ```bash
   docker-compose up -d api
   ```

## Monitoring

- **Dashboard**: Access `http://<lxc_ip>:8000/` for execution history.
- **Traces**: Access `http://<lxc_ip>:16686/` (if Jaeger is enabled) for OpenTelemetry traces.
- **Logs**: `docker-compose logs -f api`
