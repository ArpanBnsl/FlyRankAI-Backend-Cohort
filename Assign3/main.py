from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from db import get_task, initialize_database, list_tasks


class Task(BaseModel):
    id: int
    title: str
    status: bool


def serialize_task(row: dict) -> Task:
    return Task(id=row["id"], title=row["title"], status=row["done"])


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
    if task is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return serialize_task(task)
