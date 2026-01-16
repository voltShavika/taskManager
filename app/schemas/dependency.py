from pydantic import BaseModel
from datetime import datetime
from app.models.task_dependency import DependencyType
from app.schemas.task import TaskResponse
import uuid

class DependencyCreate(BaseModel):
    depends_on_task_id: uuid.UUID
    dependency_type: DependencyType = DependencyType.BLOCKING

class DependencyResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    depends_on_task_id: uuid.UUID
    dependency_type: DependencyType
    created_at: datetime

    class Config:
        from_attributes = True

class DependencyWithTask(DependencyResponse):
    depends_on_task: TaskResponse

    class Config:
        from_attributes = True

class TaskBlockingInfo(BaseModel):
    task_id: uuid.UUID
    is_blocked: bool
    blocking_dependencies: list[uuid.UUID]
    can_start: bool