from functools import lru_cache
from typing import Dict, Any
import time

in_memory_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 300  # 5 minutes

@lru_cache(maxsize=100)
def get_user_permissions(user_id: str, role: str) -> Dict[str, bool]:
    permissions = {
        "admin": {
            "can_create_teams": True,
            "can_delete_users": True,
            "can_manage_all_teams": True,
            "can_view_all_tasks": True
        },
        "manager": {
            "can_create_teams": True,
            "can_delete_users": False,
            "can_manage_all_teams": False,
            "can_view_all_tasks": False
        },
        "user": {
            "can_create_teams": False,
            "can_delete_users": False,
            "can_manage_all_teams": False,
            "can_view_all_tasks": False
        }
    }
    return permissions.get(role, permissions["user"])

def cache_set(key: str, value: Any, ttl: int = CACHE_TTL):
    in_memory_cache[key] = {
        "value": value,
        "expires": time.time() + ttl
    }

def cache_get(key: str) -> Any:
    if key in in_memory_cache:
        if time.time() < in_memory_cache[key]["expires"]:
            return in_memory_cache[key]["value"]
        else:
            del in_memory_cache[key]
    return None

def cache_clear():
    in_memory_cache.clear()