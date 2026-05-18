from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.models import (
    UserRole, RiskLevel, TestLevel, ChangeType, ChecklistStatus,
    TestResultChoice, ExecutedChoice, LogAction
)


# ─── 通用 ──────────────────────────────────────────────────
class PageResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list


# ─── 用户 ──────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    real_name: str = Field(..., max_length=100)
    email: EmailStr
    role: UserRole = UserRole.DEVELOPER
    status: bool = True


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[bool] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    real_name: str
    email: str
    role: UserRole
    status: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── 项目 ──────────────────────────────────────────────────
class ProjectCreate(BaseModel):
    project_name: str = Field(..., max_length=100)
    product_model: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    product_model: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectOut(BaseModel):
    id: int
    project_name: str
    product_model: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── 风险模块 ──────────────────────────────────────────────
class RiskModuleCreate(BaseModel):
    module_code: str = Field(..., max_length=50)
    module_name: str = Field(..., max_length=100)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class RiskModuleUpdate(BaseModel):
    module_name: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class RiskModuleOut(BaseModel):
    id: int
    module_code: str
    module_name: str
    risk_level: RiskLevel
    description: Optional[str]
    sort_order: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── 测试项 ───────────────────────────────────────────────
class TestItemCreate(BaseModel):
    test_code: str = Field(..., max_length=50)
    test_name: str = Field(..., max_length=200)
    default_level: TestLevel = TestLevel.RECOMMENDED
    default_risk_level: RiskLevel = RiskLevel.MEDIUM
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class TestItemUpdate(BaseModel):
    test_name: Optional[str] = None
    default_level: Optional[TestLevel] = None
    default_risk_level: Optional[RiskLevel] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class TestItemOut(BaseModel):
    id: int
    test_code: str
    test_name: str
    default_level: TestLevel
    default_risk_level: RiskLevel
    description: Optional[str]
    sort_order: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── 模块-测试项映射 ────────────────────────────────────────
class ModuleTestMapCreate(BaseModel):
    module_code: str
    test_code: str
    is_required: bool = False
    sort_order: int = 0
    remark: Optional[str] = None
    is_active: bool = True


class ModuleTestMapUpdate(BaseModel):
    is_required: Optional[bool] = None
    sort_order: Optional[int] = None
    remark: Optional[str] = None
    is_active: Optional[bool] = None


class ModuleTestMapOut(BaseModel):
    id: int
    module_code: str
    test_code: str
    is_required: bool
    sort_order: int
    remark: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── 认证 ──────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


# ─── 自检单 ────────────────────────────────────────────────
class ChecklistCreate(BaseModel):
    title: str = Field(..., max_length=200)
    project_id: int
    product_model: Optional[str] = None
    version_no: str = Field(..., max_length=50)
    branch_name: Optional[str] = None
    commit_id: Optional[str] = None
    mr_pr_link: Optional[str] = None
    requirement_no: Optional[str] = None
    change_type: ChangeType
    change_summary: Optional[str] = None
    risk_description: Optional[str] = None


class ChecklistUpdate(BaseModel):
    title: Optional[str] = None
    project_id: Optional[int] = None
    product_model: Optional[str] = None
    version_no: Optional[str] = None
    branch_name: Optional[str] = None
    commit_id: Optional[str] = None
    mr_pr_link: Optional[str] = None
    requirement_no: Optional[str] = None
    change_type: Optional[ChangeType] = None
    change_summary: Optional[str] = None
    risk_description: Optional[str] = None


class ChecklistModuleSelect(BaseModel):
    module_ids: List[int]


class ChecklistTestResultInput(BaseModel):
    test_result_id: int
    executed: Optional[ExecutedChoice] = None
    result: Optional[TestResultChoice] = None
    remark: Optional[str] = None


class ChecklistTestResultsUpdate(BaseModel):
    results: List[ChecklistTestResultInput]


class GenerateTestItemsRequest(BaseModel):
    module_ids: List[int]


class GenerateTestItemOut(BaseModel):
    test_item_id: int
    test_code: str
    test_name: str
    module_id: int
    module_name: str
    module_code: str
    is_required: bool
    test_level: TestLevel
    description: Optional[str]


class ReviewRequest(BaseModel):
    action: ChecklistStatus  # APPROVED or RETURNED
    comment: str = Field(..., min_length=1)


class ChecklistOut(BaseModel):
    id: int
    checklist_no: Optional[str]
    title: str
    project_id: int
    product_model: Optional[str]
    version_no: str
    branch_name: Optional[str]
    commit_id: Optional[str]
    mr_pr_link: Optional[str]
    requirement_no: Optional[str]
    change_type: ChangeType
    change_summary: Optional[str]
    risk_description: Optional[str]
    risk_level: RiskLevel
    status: ChecklistStatus
    creator_id: int
    reviewer_id: Optional[int]
    review_comment: Optional[str]
    review_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True


class ChecklistDetailOut(ChecklistOut):
    selected_modules: List[RiskModuleOut]
    test_results: List["ChecklistTestResultDetailOut"]
    creator: UserOut
    reviewer: Optional[UserOut] = None
    project: ProjectOut

    class Config:
        from_attributes = True


class ChecklistTestResultDetailOut(BaseModel):
    id: int
    test_item_id: int
    module_id: int
    is_required: bool
    test_level: TestLevel
    source_modules: Optional[str]
    executed: Optional[ExecutedChoice]
    result: Optional[TestResultChoice]
    remark: Optional[str]
    created_at: datetime
    updated_at: datetime
    test_item: TestItemOut
    module: RiskModuleOut

    class Config:
        from_attributes = True


# ─── 操作日志 ──────────────────────────────────────────────
class OperationLogOut(BaseModel):
    id: int
    operator_id: int
    operator_name: str
    business_type: str
    business_id: Optional[int]
    business_no: Optional[str]
    action: str
    detail: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── 审核记录 ──────────────────────────────────────────────
class ReviewRecordOut(BaseModel):
    id: int
    reviewer_id: int
    action: ChecklistStatus
    comment: str
    created_at: datetime
    reviewer: UserOut

    class Config:
        from_attributes = True
