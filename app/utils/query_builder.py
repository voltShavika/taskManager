from sqlalchemy.orm import Query
from sqlalchemy import and_, or_, func, text
from typing import List, Optional, Union
from datetime import date
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.task_assignment import TaskAssignment
from app.models.tag import Tag, task_tags
from app.models.team_member import TeamMember
from app.schemas.filters import TaskFilters, AdvancedTaskFilters, DateFilter, FilterOperator
import uuid

def build_date_filter(column, date_filter: DateFilter):
    conditions = []

    if date_filter.on:
        conditions.append(func.date(column) == date_filter.on)
    if date_filter.before:
        conditions.append(func.date(column) < date_filter.before)
    if date_filter.after:
        conditions.append(func.date(column) > date_filter.after)

    return and_(*conditions) if conditions else None

def build_task_query_filters(base_query: Query, filters: TaskFilters, current_user_id: uuid.UUID) -> Query:
    query = base_query
    conditions = []
    if filters.team_id:
        conditions.append(Task.team_id == filters.team_id)
    if filters.status:
        if isinstance(filters.status, list):
            conditions.append(Task.status.in_(filters.status))
        else:
            conditions.append(Task.status == filters.status)

    if filters.priority:
        if isinstance(filters.priority, list):
            conditions.append(Task.priority.in_(filters.priority))
        else:
            conditions.append(Task.priority == filters.priority)

    if filters.created_by:
        conditions.append(Task.created_by == filters.created_by)

    if filters.due_date:
        date_condition = build_date_filter(Task.due_date, filters.due_date)
        if date_condition is not None:
            conditions.append(date_condition)

    if filters.created_at:
        date_condition = build_date_filter(Task.created_at, filters.created_at)
        if date_condition is not None:
            conditions.append(date_condition)

    if filters.updated_at:
        date_condition = build_date_filter(Task.updated_at, filters.updated_at)
        if date_condition is not None:
            conditions.append(date_condition)

    if filters.search:
        search_term = f"%{filters.search}%"
        search_condition = or_(
            Task.title.ilike(search_term),
            Task.description.ilike(search_term)
        )
        conditions.append(search_condition)

    assignment_conditions = []

    if filters.assigned_to_me:
        assignment_conditions.append(TaskAssignment.user_id == current_user_id)

    if filters.assignee_ids:
        assignment_conditions.append(TaskAssignment.user_id.in_(filters.assignee_ids))

    if assignment_conditions:
        query = query.join(TaskAssignment)
        if len(assignment_conditions) == 1:
            conditions.append(assignment_conditions[0])
        else:
            conditions.append(or_(*assignment_conditions))

    tag_conditions = []

    if filters.tag_ids:
        query = query.join(task_tags).join(Tag)
        tag_conditions.append(Tag.id.in_(filters.tag_ids))

    if filters.tag_names:
        if not any([filters.tag_ids]):
            query = query.join(task_tags).join(Tag)
        tag_conditions.append(Tag.name.in_(filters.tag_names))

    if tag_conditions:
        if len(tag_conditions) == 1:
            conditions.append(tag_conditions[0])
        else:
            conditions.append(or_(*tag_conditions))

    if conditions:
        if filters.operator == FilterOperator.AND:
            query = query.filter(and_(*conditions))
        else:
            query = query.filter(or_(*conditions))

    return query

def build_advanced_task_query(
    base_query: Query,
    advanced_filters: AdvancedTaskFilters,
    current_user_id: uuid.UUID
) -> Query:
    if not advanced_filters.filters:
        return base_query

    filter_queries = []

    for filter_group in advanced_filters.filters:
        subquery = build_task_query_filters(base_query, filter_group, current_user_id)
        if subquery.whereclause is not None:
            filter_queries.append(subquery.whereclause)

    if not filter_queries:
        return base_query

    if advanced_filters.global_operator == FilterOperator.AND:
        combined_condition = and_(*filter_queries)
    else:
        combined_condition = or_(*filter_queries)

    return base_query.filter(combined_condition)

def parse_query_params_to_filters(
    team_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_ids: Optional[str] = None,
    created_by: Optional[str] = None,
    assigned_to_me: Optional[bool] = False,
    due_date_before: Optional[date] = None,
    due_date_after: Optional[date] = None,
    due_date_on: Optional[date] = None,
    created_before: Optional[date] = None,
    created_after: Optional[date] = None,
    updated_before: Optional[date] = None,
    updated_after: Optional[date] = None,
    search: Optional[str] = None,
    tag_ids: Optional[str] = None,
    tag_names: Optional[str] = None,
    operator: FilterOperator = FilterOperator.AND
) -> TaskFilters:
    def parse_list(value: Optional[str], converter=str):
        if not value:
            return None
        return [converter(item.strip()) for item in value.split(',') if item.strip()]
    parsed_status = None
    if status:
        status_list = parse_list(status)
        if len(status_list) == 1:
            parsed_status = TaskStatus(status_list[0])
        else:
            parsed_status = [TaskStatus(s) for s in status_list]

    parsed_priority = None
    if priority:
        priority_list = parse_list(priority)
        if len(priority_list) == 1:
            parsed_priority = TaskPriority(priority_list[0])
        else:
            parsed_priority = [TaskPriority(p) for p in priority_list]

    parsed_assignee_ids = None
    if assignee_ids:
        parsed_assignee_ids = [uuid.UUID(aid) for aid in parse_list(assignee_ids)]

    parsed_tag_ids = None
    if tag_ids:
        parsed_tag_ids = [uuid.UUID(tid) for tid in parse_list(tag_ids)]

    parsed_tag_names = parse_list(tag_names) if tag_names else None

    due_date_filter = None
    if any([due_date_before, due_date_after, due_date_on]):
        due_date_filter = DateFilter(
            before=due_date_before,
            after=due_date_after,
            on=due_date_on
        )

    created_at_filter = None
    if any([created_before, created_after]):
        created_at_filter = DateFilter(
            before=created_before,
            after=created_after
        )

    updated_at_filter = None
    if any([updated_before, updated_after]):
        updated_at_filter = DateFilter(
            before=updated_before,
            after=updated_after
        )

    return TaskFilters(
        team_id=uuid.UUID(team_id) if team_id else None,
        status=parsed_status,
        priority=parsed_priority,
        assignee_ids=parsed_assignee_ids,
        created_by=uuid.UUID(created_by) if created_by else None,
        assigned_to_me=assigned_to_me,
        due_date=due_date_filter,
        created_at=created_at_filter,
        updated_at=updated_at_filter,
        search=search,
        tag_ids=parsed_tag_ids,
        tag_names=parsed_tag_names,
        operator=operator
    )