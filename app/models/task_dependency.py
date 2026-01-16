import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.database import Base

class DependencyType(PyEnum):
    BLOCKING = "blocking"
    SOFT = "soft"

class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    depends_on_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    dependency_type = Column(Enum(DependencyType), default=DependencyType.BLOCKING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('task_id', 'depends_on_task_id', name='unique_task_dependency'),
    )

    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship("Task", foreign_keys=[depends_on_task_id], back_populates="blocking_tasks")

from app.models.task import Task
Task.dependencies = relationship("TaskDependency", foreign_keys="TaskDependency.task_id", back_populates="task")
Task.blocking_tasks = relationship("TaskDependency", foreign_keys="TaskDependency.depends_on_task_id", back_populates="depends_on_task")