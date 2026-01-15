from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate, TeamResponse, TeamMemberAdd, TeamMemberResponse, TeamDetailResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(team_data: TeamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_team = Team(
        name=team_data.name,
        description=team_data.description,
        created_by=current_user.id
    )

    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

@router.get("/", response_model=List[TeamResponse])
def list_user_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    teams = db.query(Team).filter(Team.created_by == current_user.id).all()
    return teams

@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_team_member(
    team_id: uuid.UUID,
    member_data: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    if team.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add members")

    user = db.query(User).filter(User.email == member_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user.id,
        TeamMember.is_active == True
    ).first()
    if existing_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already a team member")

    team_member = TeamMember(
        team_id=team_id,
        user_id=user.id,
        role=member_data.role
    )

    db.add(team_member)
    db.commit()
    db.refresh(team_member)
    return team_member

@router.get("/{team_id}", response_model=TeamDetailResponse)
def get_team_details(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    is_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id,
        TeamMember.is_active == True
    ).first()

    if team.created_by != current_user.id and not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    members = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.is_active == True
    ).all()

    team_dict = {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "created_by": team.created_by,
        "created_at": team.created_at,
        "members": members
    }
    return team_dict