from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from bson import ObjectId
from datetime import datetime
from pydantic_core import core_schema

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> core_schema.CoreSchema:
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(cls._validate),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x), when_used="json"
            ),
        )

    @classmethod
    def _validate(cls, value: Any) -> ObjectId:
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)
        raise ValueError("Invalid ObjectId")


# === Модели для создания в Swagger ===

class UserCreate(BaseModel):
    username: str
    full_name: str
    role: str
    email: str


class ProjectCreate(BaseModel):
    name: str
    members: List[str] = []


class TaskCreate(BaseModel):
    title: str
    status: str = "New"
    priority: str = "Medium"
    assignee_name: str
    project_name: str


# === Модели для чтения в Swagger ===

class User(UserCreate):
    id: PyObjectId
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class Project(ProjectCreate):
    id: PyObjectId
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class Task(TaskCreate):
    id: PyObjectId
    created_at: Optional[datetime] = None
    assignee_name: Optional[str] = None
    project_name: Optional[str] = None
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


# === Обновление моделей в Swagger ===

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    members: Optional[List[str]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_name: Optional[str] = None
    project_name: Optional[str] = None
