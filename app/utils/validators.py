from datetime import date, datetime
from typing import Optional

def validate_due_date(due_date: Optional[date]) -> bool:
    if due_date is None:
        return True
    return due_date >= date.today()

def validate_task_title(title: str) -> bool:
    return len(title.strip()) >= 1 and len(title) <= 200

def validate_team_name(name: str) -> bool:
    return len(name.strip()) >= 2 and len(name) <= 100