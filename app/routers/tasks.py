from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.task_assignment import TaskAssignment
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskDetailResponse,
    TaskAssignmentCreate, TaskAssignmentResponse, BulkTaskUpdate
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

    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    team_id: Optional[uuid.UUID] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assigned_to_me: Optional[bool] = Query(False)
):
    query = db.query(Task).join(Team).join(TeamMember).filter(
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True
    )

    if team_id:
        query = query.filter(Task.team_id == team_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to_me:
        query = query.join(TaskAssignment).filter(TaskAssignment.user_id == current_user.id)

    tasks = query.all()
    return tasks

@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    check_team_access(task.team_id, current_user, db)

    assignments = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).all()
    subtasks = db.query(Task).filter(Task.parent_task_id == task_id).all()

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

    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
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