from enum import Enum
from pydantic import BaseModel

class ClearanceLevel(str, Enum):
    PUBLIC = "PUBLIC"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"

class Role(str, Enum):
    USER = "USER"
    ANALYST = "ANALYST"
    EXPERT_REVIEWER = "EXPERT_REVIEWER"
    ADMIN = "ADMIN"

class UserContext(BaseModel):
    user_id: str
    organization_id: str
    roles: list[Role]
    clearance_level: ClearanceLevel

def check_clearance(user_level: ClearanceLevel, required_level: ClearanceLevel) -> bool:
    levels = [ClearanceLevel.PUBLIC, ClearanceLevel.RESTRICTED, ClearanceLevel.CONFIDENTIAL, ClearanceLevel.SECRET]
    try:
        user_idx = levels.index(user_level)
        req_idx = levels.index(required_level)
        return user_idx >= req_idx
    except ValueError:
        return False
