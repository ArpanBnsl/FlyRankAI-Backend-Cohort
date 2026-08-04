# Assignment 2: CONNECTING YOUR CRUD to database

A simple, high-performance CRUD (Create, Read, Update, Delete) API for managing tasks, built using **FastAPI**, backed by an **SQLite** database, and run via **Uvicorn**.

---

## Technical Design Decisions

### Why SQLite was Chosen
- **Single File Database**: All data is stored in a single file (`tasks.db`), making it extremely simple to manage, back up, and inspect.
- **Zero Setup**: Requires no separate database server installation, configuration, or background process. It works out-of-the-box using Python's built-in `sqlite3` module.
- **Survives Restarts**: Unlike in-memory data structures, data persists across application restarts and crash events.

### Database Location & Initialization
- **Location**: The database file lives at `Assign2/tasks.db`.
- **Automatic Creation**: If the database file does not exist, the application creates it automatically upon startup using a FastAPI `lifespan` event.
- **Git Ignored**: The database file is added to `.gitignore` so that each fresh clone of the repository starts with a clean database slate, avoiding conflicts with local dev states.

---

## How to Install & Run

To run the server locally on port `8000`, execute the following single command:

```bash
uv run uvicorn Assign2.main:app --reload --port 8000
```

---

## API Endpoints

| Method | Endpoint | Description | Request Body Example |
| :--- | :--- | :--- | :--- |
| **GET** | `/` | Get API root information & metadata | None |
| **GET** | `/health` | API health check | None |
| **GET** | `/tasks` | Retrieve all tasks from database | None |
| **GET** | `/tasks/{id}` | Retrieve a specific task by ID | None |
| **POST** | `/tasks` | Create a new task in database | `{"title": "New Task"}` |
| **PUT** | `/tasks/{id}` | Update task title and status | `{"title": "Updated Title", "status": true}` |
| **DELETE** | `/tasks/{id}` | Delete a task from database by ID | None |

---

## Sample curl Output

### Retrieve All Tasks (`GET /tasks`)

```http
HTTP/1.1 200 OK
date: Wed, 22 Jul 2026 00:39:10 GMT
server: uvicorn
content-length: 114
content-type: application/json

[{"id":1,"title":"task 1","status":false},{"id":2,"title":"task 2","status":true},{"id":3,"title":"task 3","status":false}]
```

---

## Database Exploration in DB Browser

Below is a screenshot of the database file `tasks.db` open inside DB Browser for SQLite:

![DB Browser Screenshot](../images/db_browser.png)

---

## Stage 4: Example SQL Query

Here is an example SQL query executed in Stage 4 to inspect the seeded tasks:

```sql
SELECT * FROM tasks WHERE status = 1;
```

**Output/Result:**
| id | title | status |
|---|---|---|
| 2 | task 2 | 1 |

