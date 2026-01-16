from typing import Generic, TypeVar, List, Dict, Any
from sqlalchemy.orm import Query
from pydantic import BaseModel
from math import ceil

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20

    def __post_init__(self):
        self.page = max(1, self.page)
        self.size = min(100, max(1, self.size))

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

def paginate_query(query: Query, page: int = 1, size: int = 20) -> Dict[str, Any]:
    page = max(1, page)
    size = min(100, max(1, size))

    total = query.count()
    pages = ceil(total / size) if total > 0 else 1

    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }