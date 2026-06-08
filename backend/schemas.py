from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    skill_type: Optional[str] = None
    tags: Optional[List[str]] = None

class SkillCreate(SkillBase):
    owner: str

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    skill_type: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    prompt_template: Optional[str] = None
    workflow_data: Optional[Dict[str, Any]] = None

class SkillResponse(SkillBase):
    id: int
    owner: str
    status: str
    visibility: str
    version: str
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SkillDetailResponse(SkillResponse):
    prompt_template: Optional[str] = None
    workflow_data: Optional[Dict[str, Any]] = None
    team_lead: Optional[str] = None
    approval_comments: Optional[str] = None
    shared_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

class SkillApprovalRequest(BaseModel):
    skill_id: int
    approval_type: str  # "team" or "company"
    team_lead: str

class SkillApprovalAction(BaseModel):
    approval_id: int
    action: str  # "approve", "reject", "request_edit"
    comments: Optional[str] = None
    reviewed_by: str

class SkillInstallationCreate(BaseModel):
    skill_id: int
    user_email: str

class SkillInstallationResponse(BaseModel):
    id: int
    skill_id: int
    user_email: str
    installed_at: datetime
    is_active: bool
    is_favorite: bool
    usage_count: int

class ListResponse(BaseModel):
    items: List[SkillResponse]
    total: int
    skip: int
    limit: int


# ───────── User Memory Schemas ──────────
class UserMemorySave(BaseModel):
    memory_type: str  # "profile", "skill", "chat", "custom", "preference"
    content: Dict[str, Any]


class UserMemoryProfileSave(BaseModel):
    full_name: str
    department: str
    role: str


class UserMemorySkillSave(BaseModel):
    skill_id: int
    skill_name: str


class UserMemoryChatSave(BaseModel):
    message: str
    context: Dict[str, Any]


class UserMemoryCustomSave(BaseModel):
    note: str
    tags: Optional[List[str]] = None


class UserMemoryResponse(BaseModel):
    id: int
    user_email: str
    memory_type: str
    content: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class UserMemoryListResponse(BaseModel):
    items: List[UserMemoryResponse]
    total: int
