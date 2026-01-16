from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional, Union
from enum import Enum
from app.models.task import TaskStatus, TaskPriority
import uuid

class FilterOperator(str, Enum):
    AND = "and"
    OR = "or"

class DateFilter(BaseModel):
    before: Optional[date] = None
    after: Optional[date] = None
    on: Optional[date] = None

class TaskFilters(BaseModel):
    team_id: Optional[uuid.UUID] = None
    status: Optional[Union[TaskStatus, List[TaskStatus]]] = None
    priority: Optional[Union[TaskPriority, List[TaskPriority]]] = None

    assigned_to_me: Optional[bool] = False
    assignee_ids: Optional[List[uuid.UUID]] = None
    created_by: Optional[uuid.UUID] = None

    due_date: Optional[DateFilter] = None
    created_at: Optional[DateFilter] = None
    updated_at: Optional[DateFilter] = None

    search: Optional[str] = None

    tag_ids: Optional[List[uuid.UUID]] = None
    tag_names: Optional[List[str]] = None

    operator: FilterOperator = FilterOperator.AND

class AdvancedTaskFilters(BaseModel):
    filters: List[TaskFilters] = Field(default_factory=list)
    global_operator: FilterOperator = FilterOperator.AND