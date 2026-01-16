from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Set
from app.models.task import Task, TaskStatus
from app.models.task_dependency import TaskDependency, DependencyType
import uuid

def has_circular_dependency(task_id: uuid.UUID, depends_on_task_id: uuid.UUID, db: Session) -> bool:
    visited = set()

    def dfs_check(current_task_id: uuid.UUID) -> bool:
        if current_task_id == task_id:
            return True
        if current_task_id in visited:
            return False

        visited.add(current_task_id)

        dependencies = db.query(TaskDependency).filter(
            TaskDependency.task_id == current_task_id
        ).all()

        for dep in dependencies:
            if dfs_check(dep.depends_on_task_id):
                return True

        return False

    return dfs_check(depends_on_task_id)

def get_blocking_dependencies(task_id: uuid.UUID, db: Session) -> List[uuid.UUID]:
    incomplete_deps = (
        db.query(TaskDependency.depends_on_task_id)
        .join(Task, TaskDependency.depends_on_task_id == Task.id)
        .filter(
            and_(
                TaskDependency.task_id == task_id,
                TaskDependency.dependency_type == DependencyType.BLOCKING,
                Task.status != TaskStatus.DONE
            )
        ).all()
    )

    return [dep[0] for dep in incomplete_deps]

def is_task_blocked(task_id: uuid.UUID, db: Session) -> bool:
    blocking_deps = get_blocking_dependencies(task_id, db)
    return len(blocking_deps) > 0

def can_task_start(task_id: uuid.UUID, db: Session) -> bool:
    return not is_task_blocked(task_id, db)

def get_tasks_that_can_be_unblocked(completed_task_id: uuid.UUID, db: Session) -> List[uuid.UUID]:
    dependent_tasks = (
        db.query(TaskDependency.task_id)
        .filter(TaskDependency.depends_on_task_id == completed_task_id)
        .all()
    )

    unblockable_tasks = []
    for task_tuple in dependent_tasks:
        task_id = task_tuple[0]
        if can_task_start(task_id, db):
            unblockable_tasks.append(task_id)

    return unblockable_tasks

def update_task_blocked_status(task_id: uuid.UUID, db: Session):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return

    is_blocked = is_task_blocked(task_id, db)

    if is_blocked and task.status not in [TaskStatus.BLOCKED, TaskStatus.DONE]:
        task.status = TaskStatus.BLOCKED
        db.commit()
    elif not is_blocked and task.status == TaskStatus.BLOCKED:
        task.status = TaskStatus.TODO
        db.commit()

def update_dependent_tasks_status(completed_task_id: uuid.UUID, db: Session):
    unblockable_tasks = get_tasks_that_can_be_unblocked(completed_task_id, db)

    for task_id in unblockable_tasks:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task and task.status == TaskStatus.BLOCKED:
            task.status = TaskStatus.TODO

    if unblockable_tasks:
        db.commit()

def validate_dependency_creation(task_id: uuid.UUID, depends_on_task_id: uuid.UUID, db: Session) -> dict:
    if task_id == depends_on_task_id:
        return {"valid": False, "error": "Task cannot depend on itself"}

    task = db.query(Task).filter(Task.id == task_id).first()
    depends_on_task = db.query(Task).filter(Task.id == depends_on_task_id).first()

    if not task:
        return {"valid": False, "error": "Task not found"}
    if not depends_on_task:
        return {"valid": False, "error": "Dependency target task not found"}

    if task.team_id != depends_on_task.team_id:
        return {"valid": False, "error": "Tasks must be in the same team"}

    existing_dependency = db.query(TaskDependency).filter(
        and_(
            TaskDependency.task_id == task_id,
            TaskDependency.depends_on_task_id == depends_on_task_id
        )
    ).first()

    if existing_dependency:
        return {"valid": False, "error": "Dependency already exists"}

    if has_circular_dependency(task_id, depends_on_task_id, db):
        return {"valid": False, "error": "Would create circular dependency"}

    return {"valid": True}