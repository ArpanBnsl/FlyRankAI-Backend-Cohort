# Assignment A3: Containerize the Task API

A FastAPI CRUD API backed by PostgreSQL. The database runs in Docker, and Docker Compose starts the full stack with persistent storage.

## Run everything

1. Copy the example configuration:

   ```bash
   cp .env.example .env
   ```

2. Replace `POSTGRES_PASSWORD` and the matching password in `DATABASE_URL` with a local development password.

3. Start the app and database:

   ```bash
   docker compose up --build
   ```

The API is available at `http://localhost:3000`. The `taskdata` Docker volume preserves tasks through `docker compose down` and the next `docker compose up`.

## Configuration

| Variable | Purpose |
| --- | --- |
| `POSTGRES_PASSWORD` | Password used by the Postgres container. |
| `POSTGRES_DB` | Database created by the Postgres container. |
| `DATABASE_URL` | Local host connection string for running the API outside Docker. |
| `DATABASE_URL_DOCKER` | Container-network connection string; it uses the `db` service name. |

`.env` is ignored by Git. Commit only `.env.example`; do not put real credentials in source control.

## API endpoints

| Method | Endpoint | Success | Description |
| --- | --- | --- | --- |
| GET | `/tasks` | 200 | List tasks from PostgreSQL. |
| GET | `/tasks/{id}` | 200 / 404 | Fetch one task. |
| POST | `/tasks` | 201 / 400 | Create a task with `title` and optional `status`. |
| PUT | `/tasks/{id}` | 200 / 400 / 404 | Replace a task title and status. |
| DELETE | `/tasks/{id}` | 204 / 404 | Delete a task. |
| GET | `/health` | 200 | Basic API health response. |

All database queries live in `db.py` and use psycopg parameter placeholders (`%s`). The physical Postgres column is `done`; responses retain A2's `status` field for API compatibility. On its first run, the app creates the `tasks` table and inserts three example rows. Later restarts do not reseed the table.

## Example request

```bash
curl -i http://localhost:3000/tasks
```

```http
HTTP/1.1 200 OK
content-type: application/json

[{"id":1,"title":"task 1","status":false},{"id":2,"title":"task 2","status":true},{"id":3,"title":"task 3","status":false}]
```

## Inspect the database

With the stack running, verify the table and rows directly in PostgreSQL:

```bash
docker compose exec db psql -U postgres -d tasks -c "\dt"
docker compose exec db psql -U postgres -d tasks -c "SELECT id, title, done FROM tasks ORDER BY id;"
```

## Local development without Compose

Start PostgreSQL using the Stage 0 command below, copy `.env.example` to `.env`, then run:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 3000
```

```bash
docker run --name taskdb -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=tasks -p 5432:5432 -v taskdata:/var/lib/postgresql/data -d postgres
```
