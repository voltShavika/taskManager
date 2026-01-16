from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.utils.pagination import paginate_query
from app.utils.query_builder import build_task_query_filters, parse_query_params_to_filters, build_advanced_task_query
from app.schemas.filters import TaskFilters, AdvancedTaskFilters, FilterOperator
import uuid
from app.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.task_assignment import TaskAssignment
from app.models.task_dependency import TaskDependency, DependencyType
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.models.tag import Tag
from app.utils.dependency_logic import update_dependent_tasks_status, is_task_blocked, get_blocking_dependencies
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskDetailResponse,
    TaskAssignmentCreate, TaskAssignmentResponse, BulkTaskUpdate,
    PaginatedTasksResponse
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

def check_team_access(team_id: uuid.UUID, current_user: User, db: Session):
    is_team_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True
    ).first()

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    if team.created_by != current_user.id and not is_team_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return team

def enrich_tasks_with_dependency_info(tasks: List[Task], db: Session) -> List[Task]:
    for task in tasks:
        task.is_blocked = is_task_blocked(task.id, db)
        blocking_count = db.query(TaskDependency).filter(
            TaskDependency.depends_on_task_id == task.id
        ).count()
        task.blocking_task_count = blocking_count
    return tasks

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_team_access(task_data.team_id, current_user, db)

    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date,
        team_id=task_data.team_id,
        created_by=current_user.id
    )

    if task_data.tag_ids:
        tags = db.query(Tag).filter(
            Tag.id.in_(task_data.tag_ids),
            Tag.team_id == task_data.team_id
        ).all()

        if len(tags) != len(task_data.tag_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some tag IDs are invalid or not from the same team"
            )

        task.tags = tags

    db.add(task)
    db.commit()
    db.refresh(task)

    task.is_blocked = is_task_blocked(task.id, db)
    task.blocking_task_count = db.query(TaskDependency).filter(
        TaskDependency.depends_on_task_id == task.id
    ).count()

    return task

@router.get("/", response_model=PaginatedTasksResponse)
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    team_id: Optional[str] = Query(None, description="Team ID or comma-separated IDs"),
    status: Optional[str] = Query(None, description="Status or comma-separated statuses (todo,in_progress,review,done,blocked)"),
    priority: Optional[str] = Query(None, description="Priority or comma-separated priorities (low,medium,high,critical)"),
    assigned_to_me: Optional[bool] = Query(False, description="Show only tasks assigned to current user"),
    assignee_ids: Optional[str] = Query(None, description="Comma-separated assignee user IDs"),
    created_by: Optional[str] = Query(None, description="Task creator user ID"),
    due_date_before: Optional[date] = Query(None, description="Tasks due before this date"),
    due_date_after: Optional[date] = Query(None, description="Tasks due after this date"),
    due_date_on: Optional[date] = Query(None, description="Tasks due on this date"),
    created_before: Optional[date] = Query(None, description="Tasks created before this date"),
    created_after: Optional[date] = Query(None, description="Tasks created after this date"),
    updated_before: Optional[date] = Query(None, description="Tasks updated before this date"),
    updated_after: Optional[date] = Query(None, description="Tasks updated after this date"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    tag_ids: Optional[str] = Query(None, description="Comma-separated tag IDs"),
    tag_names: Optional[str] = Query(None, description="Comma-separated tag names"),
    operator: FilterOperator = Query(FilterOperator.AND, description="Combine filters with AND or OR logic")
):
    base_query = db.query(Task).join(Team).join(TeamMember).filter(
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True
    )

    filters = parse_query_params_to_filters(
        team_id=team_id,
        status=status,
        priority=priority,
        assignee_ids=assignee_ids,
        created_by=created_by,
        assigned_to_me=assigned_to_me,
        due_date_before=due_date_before,
        due_date_after=due_date_after,
        due_date_on=due_date_on,
        created_before=created_before,
        created_after=created_after,
        updated_before=updated_before,
        updated_after=updated_after,
        search=search,
        tag_ids=tag_ids,
        tag_names=tag_names,
        operator=operator
    )

    filtered_query = build_task_query_filters(base_query, filters, current_user.id)

    return paginate_query(filtered_query, page, size, enrich_tasks_with_dependency_info, db)

@router.post("/search", response_model=PaginatedTasksResponse)
def advanced_search_tasks(
    advanced_filters: AdvancedTaskFilters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size")
):
    base_query = db.query(Task).join(Team).join(TeamMember).filter(
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True
    )

    filtered_query = build_advanced_task_query(base_query, advanced_filters, current_user.id)

    return paginate_query(filtered_query, page, size, enrich_tasks_with_dependency_info, db)

@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    check_team_access(task.team_id, current_user, db)

    assignments = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).all()
    subtasks = db.query(Task).filter(Task.parent_task_id == task_id).all()

    task.is_blocked = is_task_blocked(task.id, db)
    task.blocking_task_count = db.query(TaskDependency).filter(
        TaskDependency.depends_on_task_id == task.id
    ).count()

    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "parent_task_id": task.parent_task_id,
        "team_id": task.team_id,
        "created_by": task.created_by,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "is_blocked": task.is_blocked,
        "blocking_task_count": task.blocking_task_count,
        "assignments": assignments,
        "subtasks": subtasks
    }
    return task_dict

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: uuid.UUID,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    check_team_access(task.team_id, current_user, db)

    update_data = task_update.dict(exclude_unset=True)
    old_status = task.status

    if 'tag_ids' in update_data:
        tag_ids = update_data.pop('tag_ids')
        if tag_ids:
            tags = db.query(Tag).filter(
                Tag.id.in_(tag_ids),
                Tag.team_id == task.team_id
            ).all()

            if len(tags) != len(tag_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some tag IDs are invalid or not from the same team"
                )

            task.tags = tags
        else:
            task.tags = []

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    if old_status != TaskStatus.DONE and task.status == TaskStatus.DONE:
        update_dependent_tasks_status(task.id, db)

    task.is_blocked = is_task_blocked(task.id, db)
    task.blocking_task_count = db.query(TaskDependency).filter(
        TaskDependency.depends_on_task_id == task.id
    ).count()

    return task

@router.post("/{task_id}/assignments", response_model=TaskAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_task(
    task_id: uuid.UUID,
    assignment_data: TaskAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    check_team_access(task.team_id, current_user, db)

    user = db.query(User).filter(User.id == assignment_data.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    is_team_member = db.query(TeamMember).filter(
        TeamMember.team_id == task.team_id,
        TeamMember.user_id == assignment_data.user_id,
        TeamMember.is_active == True
    ).first()
    if not is_team_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not a team member")

    existing_assignment = db.query(TaskAssignment).filter(
        TaskAssignment.task_id == task_id,
        TaskAssignment.user_id == assignment_data.user_id
    ).first()
    if existing_assignment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already assigned to task")

    assignment = TaskAssignment(
        task_id=task_id,
        user_id=assignment_data.user_id,
        role=assignment_data.role
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

@router.post("/{task_id}/subtasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_subtask(
    task_id: uuid.UUID,
    subtask_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    parent_task = db.query(Task).filter(Task.id == task_id).first()
    if not parent_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent task not found")

    check_team_access(parent_task.team_id, current_user, db)

    subtask = Task(
        title=subtask_data.title,
        description=subtask_data.description,
        status=subtask_data.status,
        priority=subtask_data.priority,
        due_date=subtask_data.due_date,
        parent_task_id=task_id,
        team_id=parent_task.team_id,
        created_by=current_user.id
    )

    db.add(subtask)
    db.commit()
    db.refresh(subtask)

    subtask.is_blocked = is_task_blocked(subtask.id, db)
    subtask.blocking_task_count = db.query(TaskDependency).filter(
        TaskDependency.depends_on_task_id == subtask.id
    ).count()

    return subtask

@router.post("/bulk-update")
def bulk_update_tasks(
    bulk_data: BulkTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = []

    for update_item in bulk_data.task_updates:
        try:
            task_id = uuid.UUID(update_item.get("task_id"))
            task = db.query(Task).filter(Task.id == task_id).first()

            if not task:
                results.append({"task_id": str(task_id), "success": False, "error": "Task not found"})
                continue

            try:
                check_team_access(task.team_id, current_user, db)
            except HTTPException as e:
                results.append({"task_id": str(task_id), "success": False, "error": e.detail})
                continue

            update_fields = {k: v for k, v in update_item.items() if k != "task_id" and v is not None}

            for field, value in update_fields.items():
                if hasattr(task, field):
                    setattr(task, field, value)

            db.commit()
            results.append({"task_id": str(task_id), "success": True})

        except Exception as e:
            results.append({"task_id": update_item.get("task_id", "unknown"), "success": False, "error": str(e)})

    return {"results": results}

@router.get("/{task_id}/assignments", response_model=List[TaskAssignmentResponse])
def list_task_assignments(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    check_team_access(task.team_id, current_user, db)

    assignments = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).all()
    return assignments

@router.delete("/{task_id}/assignments/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task_assignment(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    check_team_access(task.team_id, current_user, db)

    assignment = db.query(TaskAssignment).filter(
        TaskAssignment.task_id == task_id,
        TaskAssignment.user_id == user_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    db.delete(assignment)
    db.commit()

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    check_team_access(task.team_id, current_user, db)

    if task.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only task creator can delete")

    subtasks = db.query(Task).filter(Task.parent_task_id == task_id).all()
    for subtask in subtasks:
        subtask.parent_task_id = None

    db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).delete()
    db.delete(task)
    db.commit()