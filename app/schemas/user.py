from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import UserRole
import uuid

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserResponse(UserBase):
    id: uuid.UUID
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True