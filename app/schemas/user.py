from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.models.user import UserRole
from app.utils.pagination import PaginatedResponse
import uuid

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(UserBase):
    id: uuid.UUID
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedUsersResponse(PaginatedResponse[UserResponse]):
    pass