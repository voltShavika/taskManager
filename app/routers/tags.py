from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.tag import Tag
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.dependencies import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])

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

@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_team_access(tag_data.team_id, current_user, db)

    existing_tag = db.query(Tag).filter(
        Tag.team_id == tag_data.team_id,
        Tag.name == tag_data.name
    ).first()
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists in team"
        )

    tag = Tag(
        name=tag_data.name,
        color=tag_data.color,
        team_id=tag_data.team_id,
        created_by=current_user.id
    )

    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@router.get("/", response_model=List[TagResponse])
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    team_id: uuid.UUID = Query(..., description="Team ID to list tags for")
):
    check_team_access(team_id, current_user, db)

    tags = db.query(Tag).filter(Tag.team_id == team_id).all()
    return tags

@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    check_team_access(tag.team_id, current_user, db)
    return tag

@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: uuid.UUID,
    tag_update: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    check_team_access(tag.team_id, current_user, db)

    if tag_update.name and tag_update.name != tag.name:
        existing_tag = db.query(Tag).filter(
            Tag.team_id == tag.team_id,
            Tag.name == tag_update.name,
            Tag.id != tag_id
        ).first()
        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists in team"
            )

    for field, value in tag_update.dict(exclude_unset=True).items():
        setattr(tag, field, value)

    db.commit()
    db.refresh(tag)
    return tag

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    check_team_access(tag.team_id, current_user, db)

    db.delete(tag)
    db.commit()