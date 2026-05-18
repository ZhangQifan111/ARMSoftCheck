from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    REVIEWER = "REVIEWER"
    TESTER = "TESTER"


class RiskLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TestLevel(str, enum.Enum):
    REQUIRED = "REQUIRED"
    RECOMMENDED = "RECOMMENDED"


class ChangeType(str, enum.Enum):
    BUGFIX = "BUGFIX"
    FEATURE = "FEATURE"
    REFACTOR = "REFACTOR"
    OPTIMIZATION = "OPTIMIZATION"
    OTHER = "OTHER"


class ChecklistStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    RETURNED = "RETURNED"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"


class TestResultChoice(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NA = "NA"


class ExecutedChoice(str, enum.Enum):
    YES = "YES"
    NO = "NO"
    NA = "NA"


class LogAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    RETURN = "RETURN"


# ─── 用户表 ────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    real_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    status = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ─── 项目表 ────────────────────────────────────────────────
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(100), nullable=False)
    product_model = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ─── 风险模块表 ────────────────────────────────────────────
class RiskModule(Base):
    __tablename__ = "risk_modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_code = Column(String(50), unique=True, nullable=False, index=True)
    module_name = Column(String(100), nullable=False)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM, nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ─── 测试项表 ──────────────────────────────────────────────
class TestItem(Base):
    __tablename__ = "test_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_code = Column(String(50), unique=True, nullable=False, index=True)
    test_name = Column(String(200), nullable=False)
    default_level = Column(Enum(TestLevel), default=TestLevel.RECOMMENDED, nullable=False)
    default_risk_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM, nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ─── 模块-测试项映射表 ─────────────────────────────────────
class ModuleTestMap(Base):
    __tablename__ = "module_test_maps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_code = Column(String(50), ForeignKey("risk_modules.module_code"), nullable=False, index=True)
    test_code = Column(String(50), ForeignKey("test_items.test_code"), nullable=False, index=True)
    is_required = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0)
    remark = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_module_test_unique", "module_code", "test_code", unique=True),
    )


# ─── 编号序列表 ────────────────────────────────────────────
class ChecklistSequence(Base):
    __tablename__ = "checklist_sequence"

    id = Column(Integer, primary_key=True)
    date_str = Column(String(8), unique=True, nullable=False)
    current_value = Column(Integer, default=0, nullable=False)


# ─── 自检单主表 ────────────────────────────────────────────
class Checklist(Base):
    __tablename__ = "checklists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checklist_no = Column(String(30), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    product_model = Column(String(100), nullable=True)
    version_no = Column(String(50), nullable=False)
    branch_name = Column(String(100), nullable=True)
    commit_id = Column(String(100), nullable=True)
    mr_pr_link = Column(String(500), nullable=True)
    requirement_no = Column(String(100), nullable=True)
    change_type = Column(Enum(ChangeType), nullable=False)
    change_summary = Column(Text, nullable=True)
    risk_description = Column(Text, nullable=True)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW, nullable=False)
    status = Column(Enum(ChecklistStatus), default=ChecklistStatus.DRAFT, nullable=False)

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    review_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime, nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    project = relationship("Project")
    selected_modules = relationship("ChecklistModule", back_populates="checklist", cascade="all, delete-orphan")
    test_results = relationship("ChecklistTestResult", back_populates="checklist", cascade="all, delete-orphan")
    reviews = relationship("ChecklistReview", back_populates="checklist", cascade="all, delete-orphan")


# ─── 自检单-模块关联表 ─────────────────────────────────────
class ChecklistModule(Base):
    __tablename__ = "checklist_modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("risk_modules.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    module = relationship("RiskModule")
    checklist = relationship("Checklist", back_populates="selected_modules")


# ─── 自检单-测试结果表 ─────────────────────────────────────
class ChecklistTestResult(Base):
    __tablename__ = "checklist_test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    test_item_id = Column(Integer, ForeignKey("test_items.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("risk_modules.id"), nullable=False)
    is_required = Column(Boolean, default=False)
    test_level = Column(Enum(TestLevel), nullable=False)
    source_modules = Column(String(500), nullable=True)  # 逗号分隔的模块名

    executed = Column(Enum(ExecutedChoice), nullable=True)
    result = Column(Enum(TestResultChoice), nullable=True)
    remark = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    test_item = relationship("TestItem")
    module = relationship("RiskModule")
    checklist = relationship("Checklist", back_populates="test_results")


# ─── 自检单审核记录表 ──────────────────────────────────────
class ChecklistReview(Base):
    __tablename__ = "checklist_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(Enum(ChecklistStatus), nullable=False)  # APPROVED / RETURNED
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    checklist = relationship("Checklist", back_populates="reviews")
    reviewer = relationship("User")


# ─── 操作日志表 ────────────────────────────────────────────
class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    operator_name = Column(String(100), nullable=False)
    business_type = Column(String(50), nullable=False, index=True)
    business_id = Column(Integer, nullable=True)
    business_no = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    operator = relationship("User")
