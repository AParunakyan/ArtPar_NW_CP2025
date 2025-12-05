from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import models
from database import get_db

app = FastAPI(
    title="Task Tracker",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === USERS ===
@app.get("/users", response_model=List[models.User])
async def get_users(db=Depends(get_db)):
    return [models.User(**doc, id=str(doc["_id"])) for doc in db.users.find()]

@app.post("/users", response_model=models.User)
async def create_user(user: models.UserCreate, db=Depends(get_db)):
    result = db.users.insert_one(user.model_dump())
    created = db.users.find_one({"_id": result.inserted_id})

    return models.User(
        id=str(created["_id"]),
        username=created["username"],
        full_name=created["full_name"],
        role=created["role"],
        email=created["email"]
    )
    
@app.delete("/users")
async def delete_user(user_id: str, db=Depends(get_db)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Неверный формат ID пользователя")
    result = db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"detail": "Пользователь успешно удалён", "id": user_id}


# === PROJECTS ===
@app.get("/projects", response_model=List[models.Project])
async def get_projects(db=Depends(get_db)):
    projects = []
    for doc in db.projects.find():
        doc["id"] = str(doc["_id"])
        doc["members"] = [str(m) for m in doc.get("members", [])]
        projects.append(models.Project(**doc))
    return projects

@app.post("/projects", response_model=models.Project)
async def create_project(project: models.ProjectCreate, db=Depends(get_db)):
    member_ids = []
    for username in project.members:
        user = db.users.find_one({"username": username})
        if not user:
            raise HTTPException(
                status_code=400,
                detail=f"Пользователь '{username}' не найден"
            )
        member_ids.append(user["_id"])

    data = {
        "name": project.name,
        "members": member_ids
    }

    result = db.projects.insert_one(data)
    created = db.projects.find_one({"_id": result.inserted_id})

    return models.Project(
        id=str(created["_id"]),
        name=created["name"],
        members=[str(m) for m in created.get("members", [])]
    )

@app.delete("/projects")
async def delete_project(project_id: str, db=Depends(get_db)):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Неверный формат ID")
    project = db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    db.tasks.delete_many({"project": ObjectId(project_id)})
    db.projects.delete_one({"_id": ObjectId(project_id)})
    return {
        "detail": "Проект и все его задачи успешно удалены",
        "project_id": project_id,
        "project_name": project.get("name", "Без имени")
    }


# === TASKS ===
@app.get("/tasks", response_model=List[models.Task])
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    db=Depends(get_db)
):
    query = {}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if assignee and ObjectId.is_valid(assignee):
        query["assignee"] = ObjectId(assignee)

    tasks = []
    for doc in db.tasks.find(query):
        user = db.users.find_one({"_id": doc["assignee"]})
        project = db.projects.find_one({"_id": doc["project"]})
        task_data = {
            "id": str(doc["_id"]),
            "title": doc["title"],
            "status": doc["status"],
            "priority": doc["priority"],
            "assignee": str(doc["assignee"]),
            "project": str(doc["project"]),
            "created_at": doc.get("created_at"),
            "assignee_name": user["full_name"] if user else "Неизвестно",
            "project_name": project["name"] if project else "Без проекта"
        }
        tasks.append(models.Task(**task_data))
    return tasks

@app.get("/tasks/{task_id}", response_model=models.Task)
async def get_task_by_id(task_id: str, db=Depends(get_db)):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Неверный формат ID")

    task_doc = db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task_doc:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    user = db.users.find_one({"_id": task_doc["assignee"]})
    project = db.projects.find_one({"_id": task_doc["project"]})

    response_data = {
        "id": str(task_doc["__id"]),
        "title": task_doc["title"],
        "status": task_doc["status"],
        "priority": task_doc["priority"],
        "assignee": str(task_doc["assignee"]),
        "project": str(task_doc["project"]),
        "created_at": task_doc.get("created_at"),
        "assignee_name": user["full_name"] if user else "Неизвестно",
        "project_name": project["name"] if project else "Без проекта"
    }
    return models.Task(**response_data)

@app.post("/tasks", response_model=models.Task)
async def create_task(task: models.TaskCreate, db=Depends(get_db)):
    user = db.users.find_one({"username": task.assignee_name})
    if not user:
        raise HTTPException(status_code=400, detail=f"Пользователь '{task.assignee_name}' не найден")

    project = db.projects.find_one({"name": task.project_name})
    if not project:
        raise HTTPException(status_code=400, detail=f"Проект '{task.project_name}' не найден")

    data = {
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "assignee": user["_id"],
        "project": project["_id"],
        "created_at": datetime.utcnow()
    }

    result = db.tasks.insert_one(data)
    created_task = db.tasks.find_one({"_id": result.inserted_id})

    response_data = {
        "id": str(created_task["_id"]),
        "title": created_task["title"],
        "status": created_task["status"],
        "priority": created_task["priority"],
        "assignee": str(created_task["assignee"]),
        "project": str(created_task["project"]),
        "created_at": created_task["created_at"],
        "assignee_name": user["full_name"],
        "project_name": project["name"]
    }

    return models.Task(**response_data)
    
@app.delete("/tasks")
async def delete_task(task_id: str, db=Depends(get_db)):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Неверный формат ID")
    result = db.tasks.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {"detail": "Задача успешно удалена", "task_id": task_id}


# === SUMMARY ===
@app.get("/summary/projects")
async def project_summary(db=Depends(get_db)):
    pipeline = [
        {"$lookup": {
            "from": "projects",
            "localField": "project",
            "foreignField": "_id",
            "as": "project_doc"
        }},
        {"$lookup": {
            "from": "users",
            "localField": "assignee",
            "foreignField": "_id",
            "as": "user_doc"
        }},
        {"$project": {
            "_id": {"$toString": "$_id"},
            "project_name": {"$arrayElemAt": ["$project_doc.name", 0]},
            "title": 1,
            "status": 1,
            "assignee_name": {"$arrayElemAt": ["$user_doc.full_name", 0]}
        }},
        {"$sort": {"project_name": 1, "title": 1}}
    ]
    result = list(db.tasks.aggregate(pipeline))
    return result


@app.get("/summary/user/{user_id}")
async def user_summary(user_id: str, db=Depends(get_db)):
    if not ObjectId.is_valid(user_id):
        return []

    pipeline = [
        {"$match": {"assignee": ObjectId(user_id)}},
        {"$lookup": {
            "from": "projects",
            "localField": "project",
            "foreignField": "_id",
            "as": "project_doc"
        }},
        {"$lookup": {
            "from": "users",
            "localField": "assignee",
            "foreignField": "_id",
            "as": "user_doc"
        }},
        {"$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "title": 1,
            "project_name": {"$arrayElemAt": ["$project_doc.name", 0]}
        }},
        {"$sort": {"project_name": 1, "title": 1}}
    ]
    result = list(db.tasks.aggregate(pipeline))
    return result
