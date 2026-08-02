## Containerized Stack & Architecture Verification

This application uses **PostgreSQL 16** and **Redis 7** fully orchestrated via Docker Compose.

### Architecture Proof (Repository Swap)
The underlying storage was migrated from SQLite to a containerized PostgreSQL database without modifying any application routes or core domain/service interfaces. Only `database.py` and environment settings were adjusted.

### Persistence Verification Procedure
Persistence was verified by completing the following sequence:
1. Executed `docker compose up -d`.
2. Created a new record via `POST /tasks`: `{"title": "Persistence Test Task"}` (Assigned ID 4).
3. Tear down the stack using `docker compose down`.
4. Re-launched the stack using `docker compose up -d`.
5. Called `GET /tasks` and confirmed ID 4 remained intact due to the `postgres_data` Docker volume.

### Stretch Goals
- **Redis Cache:** Integrated into `docker-compose.yml` and pinged upon startup.
- **Query Optimization:** Added an index on `task(title)` (`idx_task_title`) verified via `EXPLAIN ANALYZE`.