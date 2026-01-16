from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#007bff", pattern="^#[0-9A-Fa-f]{6}$")

class TagCreate(TagBase):
    team_id: uuid.UUID

class TagResponse(TagBase):
    id: uuid.UUID
    team_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")