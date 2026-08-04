import sqlite3
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException, FastAPI
from contextlib import asynccontextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR/ "tasks.db"

def db_init():
    seed_mock = DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        status BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    
    if not seed_mock:
        for task in tasks:
            cursor.execute("""
                INSERT INTO tasks (id,title,status)
                VALUES(?, ?, ?)
                """, (task.id,task.title,task.status)
            )
    conn.commit()
    conn.close()




class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    status: bool

class Task(BaseModel):
    id: int
    title: str
    status: bool

tasks = [
    Task(id=1, title="task 1", status=False),
    Task(id=2, title="task 2", status=True),
    Task(id=3, title="task 3", status=False)
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_init()
    yield


app = FastAPI(lifespan=lifespan)

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    res = cursor.execute("SELECT * FROM tasks")
    result = [
        Task(id =row[0], title=row[1],status=row[2]) for row in res.fetchall()
    ]
    conn.close()
    return result

@app.get("/tasks/{id}")
def get_tasks_by_id(id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    res = cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    result = res.fetchone()

    if result is not None:
        return Task(id =result[0],title=result[1],status=result[2])
    conn.close()
    raise HTTPException(status_code=404, detail="Task not found")



@app.post("/tasks")
def create_tasks(data: TaskCreate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    res = cursor.execute("INSERT INTO tasks (title) VALUES (?)",(data.title,))
    id = res.lastrowid
    conn.commit()
    conn.close()
    return Task(id =id,title=data.title,status=False)

@app.put("/tasks/{id}")
def update_tasks(id: int, data: TaskUpdate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    res = cursor.execute("UPDATE tasks SET title =? , status = ? WHERE id = ? ",(data.title,data.status,id))
    conn.commit()
    conn.close()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return Task(id =id,title=data.title,status=data.status)
    

@app.delete("/tasks/{id}")
def delete_tasks(id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    res = cursor.execute("DELETE FROM tasks WHERE id = ?",(id,))
    conn.commit()
    conn.close()
    if res.rowcount == 0:
        raise HTTPException(status_code=404,detail="Task not found")
    return {"message": "task deleted successfully"}
    


