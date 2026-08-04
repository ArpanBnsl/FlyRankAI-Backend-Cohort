# Assignment 1: Task CRUD API

A simple, high-performance CRUD (Create, Read, Update, Delete) API for managing tasks, built using **FastAPI** and run via **Uvicorn**.

---

## How to Install & Run

To run the server locally on port `8000`, execute the following single command:

```bash
uv run uvicorn Assign1.main:app --reload --port 8000
```

---

## API Endpoints

| Method | Endpoint | Description | Request Body Example |
| :--- | :--- | :--- | :--- |
| **GET** | `/` | Get API root information & metadata | None |
| **GET** | `/health` | API health check | None |
| **GET** | `/tasks` | Retrieve all tasks | None |
| **GET** | `/tasks/{id}` | Retrieve a specific task by ID | None |
| **POST** | `/tasks` | Create a new task | `{"title": "New Task"}` |
| **PUT** | `/tasks/{id}` | Update task title and/or status | `{"title": "Updated Title", "status": true}` |
| **DELETE** | `/tasks/{id}` | Delete a task by ID | None |

---

## Sample curl Output

### Retrieve All Tasks (`GET /tasks`)

```http
HTTP/1.1 200 OK
date: Mon, 20 Jul 2026 10:48:42 GMT
server: uvicorn
content-length: 114
content-type: application/json

{"1":{"title":"task 1","status":false},"2":{"title":"task 2","status":true},"3":{"title":"task 3","status":false}}
```

---

## Swagger UI Documentation Screenshot

Below is the Swagger UI API documentation page for the Task API.

![Swagger UI Screenshot](/images/swagger.png)
