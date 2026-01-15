import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.database import Base

class TeamRole(PyEnum):
    ADMIN = "admin"
    LEAD = "lead"
    MEMBER = "member"

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(Enum(TeamRole), default=TeamRole.MEMBER)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

from app.models.team import Team
from app.models.user import User

Team.members = relationship("TeamMember", back_populates="team")
User.team_memberships = relationship("TeamMember", back_populates="user")