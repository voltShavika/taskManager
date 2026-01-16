import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True)
)

class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, index=True)
    color = Column(String(7), default="#007bff")  # Hex color code
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    team = relationship("Team", back_populates="tags")
    creator = relationship("User", back_populates="created_tags")
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")

from app.models.team import Team
from app.models.user import User

Team.tags = relationship("Tag", back_populates="team")
User.created_tags = relationship("Tag", back_populates="creator")