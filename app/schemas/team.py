from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List
from app.models.team_member import TeamRole
import uuid

class TeamBase(BaseModel):
    name: str
    description: str = None

class TeamCreate(TeamBase):
    pass

class TeamMemberAdd(BaseModel):
    email: EmailStr
    role: TeamRole = TeamRole.MEMBER

class TeamMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: TeamRole
    joined_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class TeamResponse(TeamBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TeamDetailResponse(TeamBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    members: List[TeamMemberResponse] = []

    class Config:
        from_attributes = True