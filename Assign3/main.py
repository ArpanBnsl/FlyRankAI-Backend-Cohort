from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from db import (
    create_task,
    delete_task,
    get_task,
    initialize_database,
    list_tasks,
    update_task,
)


class Task(BaseModel):
    id: int
    title: str
    status: bool


class TaskPayload(BaseModel):
    title: str
    status: bool = False


def serialize_task(row: dict) -> Task:
    return Task(id=row["id"], title=row["title"], status=row["done"])


def valid_payload(payload: TaskPayload) -> bool:
    return bool(payload.title.strip())


def not_found() -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": "Task not found"})


def invalid_title() -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "Title is required"})


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Postgres Task API", lifespan=lifespan)


@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def get_health():
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def read_tasks():
    return [serialize_task(row) for row in list_tasks()]


@app.get("/tasks/{task_id}", response_model=Task)
def read_task(task_id: int):
    task = get_task(task_id)
    return not_found() if task is None else serialize_task(task)


@app.post("/tasks", response_model=Task, status_code=201)
def add_task(payload: TaskPayload):
    if not valid_payload(payload):
        return invalid_title()
    return serialize_task(create_task(payload.title.strip(), payload.status))


@app.put("/tasks/{task_id}", response_model=Task)
def edit_task(task_id: int, payload: TaskPayload):
    if not valid_payload(payload):
        return invalid_title()
    task = update_task(task_id, payload.title.strip(), payload.status)
    return not_found() if task is None else serialize_task(task)


@app.delete("/tasks/{task_id}", status_code=204)
def remove_task(task_id: int):
    if not delete_task(task_id):
        return not_found()
    return Response(status_code=204)
