# Assignment A3: Containerize the Task API

This assignment moves the task CRUD API from SQLite to PostgreSQL and runs the database in Docker.

## Stage 0: Start PostgreSQL locally

With Docker Desktop running, start a PostgreSQL container with persistent storage:

```bash
docker run --name taskdb -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=tasks -p 5432:5432 -v taskdata:/var/lib/postgresql/data -d postgres
```

Verify it with:

```bash
docker ps
docker exec -it taskdb psql -U postgres -d tasks
```

The remaining stages add the API connection, CRUD operations, and Compose configuration.
