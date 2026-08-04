from contextlib import asynccontextmanager

from fastapi import FastAPI

from db import initialize_database


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
