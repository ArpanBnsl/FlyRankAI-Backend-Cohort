from pydantic import BaseModel
from fastapi import HTTPException
from pydantic import ValidationError
from fastapi import FastAPI


class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str | None = None
    status: bool | None = None

class Task(BaseModel):
    title: str
    status: bool

tasks = {
    1: Task(title="task 1", status=False),
    2: Task(title="task 2", status=True),
    3: Task(title="task 3", status=False)
}
app = FastAPI()

@app.get("/")
def read_root():
    return {"name": "Task API",
            "version": "1.0",
            "endpoints": ["/tasks"]
        }

@app.get("/health")
def get_health():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{id}")
def get_tasks_by_id(id: int):
    if id in tasks:
        return {id: tasks[id]}
    raise HTTPException(status_code=404, detail="Task not found")

def provide_new_id():
    return len(tasks)+1

@app.post("/tasks")
def create_tasks(data: TaskCreate):
    id = provide_new_id()
    tasks[id] = Task(title=data.title,status=False)
    return {id: data.title}

@app.put("/tasks/{id}")
def update_tasks(id: int, data: TaskUpdate):
    if id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    if data.title is not None:
        tasks[id].title = data.title
    if data.status is not None:
        tasks[id].status = data.status
    return {id: tasks[id]}  

@app.delete("/tasks/{id}")
def delete_tasks(id: int):
    if id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[id]
    return {"message": "task deleted successfully"}
    


