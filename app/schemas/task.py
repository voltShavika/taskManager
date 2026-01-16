from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Optional
from app.models.task import TaskStatus, TaskPriority
from app.utils.pagination import PaginatedResponse
from app.schemas.tag import TagResponse
import uuid

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None

class TaskCreate(TaskBase):
    team_id: uuid.UUID
    tag_ids: Optional[List[uuid.UUID]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    tag_ids: Optional[List[uuid.UUID]] = None

class TaskAssignmentCreate(BaseModel):
    user_id: uuid.UUID
    role: str = "assignee"

class TaskAssignmentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    assigned_at: datetime
    role: str

    class Config:
        from_attributes = True

class TaskResponse(TaskBase):
    id: uuid.UUID
    parent_task_id: Optional[uuid.UUID]
    team_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True

class TaskDetailResponse(TaskResponse):
    assignments: List[TaskAssignmentResponse] = []
    subtasks: List["TaskResponse"] = []

    class Config:
        from_attributes = True

class BulkTaskUpdate(BaseModel):
    task_updates: List[dict] = Field(..., min_items=1)

class PaginatedTasksResponse(PaginatedResponse[TaskResponse]):
    pass