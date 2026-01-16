from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.task import Task
from app.models.task_dependency import TaskDependency
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.dependency import (
    DependencyCreate, DependencyResponse, DependencyWithTask, TaskBlockingInfo
)
from app.dependencies import get_current_user
from app.utils.dependency_logic import (
    validate_dependency_creation, update_task_blocked_status,
    get_blocking_dependencies, can_task_start, is_task_blocked
)

router = APIRouter(prefix="/tasks", tags=["dependencies"])

def check_task_access(task_id: uuid.UUID, current_user: User, db: Session):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    is_team_member = db.query(TeamMember).filter(
        TeamMember.team_id == task.team_id,
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True
    ).first()

    if not is_team_member and task.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return task

@router.post("/{task_id}/dependencies", response_model=DependencyResponse, status_code=status.HTTP_201_CREATED)
def add_task_dependency(
    task_id: uuid.UUID,
    dependency_data: DependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_task_access(task_id, current_user, db)
    check_task_access(dependency_data.depends_on_task_id, current_user, db)

    validation = validate_dependency_creation(task_id, dependency_data.depends_on_task_id, db)
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation["error"]
        )

    dependency = TaskDependency(
        task_id=task_id,
        depends_on_task_id=dependency_data.depends_on_task_id,
        dependency_type=dependency_data.dependency_type
    )

    db.add(dependency)
    db.commit()
    db.refresh(dependency)

    update_task_blocked_status(task_id, db)

    return dependency

@router.get("/{task_id}/dependencies", response_model=List[DependencyWithTask])
def get_task_dependencies(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_task_access(task_id, current_user, db)

    dependencies = (
        db.query(TaskDependency)
        .filter(TaskDependency.task_id == task_id)
        .all()
    )

    return dependencies

@router.get("/{task_id}/blocking", response_model=List[DependencyResponse])
def get_tasks_blocked_by_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_task_access(task_id, current_user, db)

    blocking_dependencies = (
        db.query(TaskDependency)
        .filter(TaskDependency.depends_on_task_id == task_id)
        .all()
    )

    return blocking_dependencies

@router.get("/{task_id}/status", response_model=TaskBlockingInfo)
def get_task_blocking_status(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_task_access(task_id, current_user, db)

    blocking_deps = get_blocking_dependencies(task_id, db)
    is_blocked = is_task_blocked(task_id, db)
    can_start = can_task_start(task_id, db)

    return TaskBlockingInfo(
        task_id=task_id,
        is_blocked=is_blocked,
        blocking_dependencies=blocking_deps,
        can_start=can_start
    )

@router.delete("/{task_id}/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task_dependency(
    task_id: uuid.UUID,
    dependency_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_task_access(task_id, current_user, db)

    dependency = db.query(TaskDependency).filter(
        TaskDependency.id == dependency_id,
        TaskDependency.task_id == task_id
    ).first()

    if not dependency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dependency not found")

    db.delete(dependency)
    db.commit()

    update_task_blocked_status(task_id, db)