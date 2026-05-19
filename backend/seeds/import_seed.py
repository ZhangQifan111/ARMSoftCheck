"""
种子数据导入脚本
支持幂等导入：重复执行不会产生重复数据
"""
import os, sys, csv, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.models import (
    User, Project, RiskModule, TestItem, ModuleTestMap,
    UserRole, RiskLevel, TestLevel
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


def get_seed_path(filename: str) -> Path:
    base = os.environ.get("SEED_DATA_PATH", "/app/seeds")
    path = Path(base) / filename
    if not path.exists():
        # 尝试 seed_templates
        path = Path(__file__).parent.parent / "seed_templates" / filename
    return path


def read_csv(filename: str) -> list[dict]:
    path = get_seed_path(filename)
    if not path.exists():
        logger.warning(f"Seed 文件不存在: {path}，跳过")
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def import_users(session):
    rows = read_csv("users_seed.csv")
    if not rows:
        logger.warning("users_seed.csv 无数据，跳过")
        return
    for row in rows:
        existing = session.query(User).filter_by(username=row["username"]).first()
        if existing:
            logger.info(f"用户已存在，跳过: {row['username']}")
            continue
        user = User(
            username=row["username"],
            hashed_password=get_password_hash(row["password"]),
            real_name=row["real_name"],
            email=row["email"],
            role=UserRole(row["role"]),
            status=bool(int(row.get("status", 1))),
        )
        session.add(user)
        logger.info(f"导入用户: {user.username}({user.role.value})")
    session.commit()


def import_projects(session):
    rows = read_csv("projects_seed.csv")
    if not rows:
        return
    for row in rows:
        existing = session.query(Project).filter_by(project_name=row["project_name"]).first()
        if existing:
            continue
        project = Project(
            project_name=row["project_name"],
            product_model=row.get("product_model", ""),
            is_active=bool(int(row.get("is_active", 1))),
        )
        session.add(project)
        logger.info(f"导入项目: {project.project_name}")
    session.commit()


def import_risk_modules(session):
    rows = read_csv("risk_modules_seed.csv")
    if not rows:
        return
    for row in rows:
        existing = session.query(RiskModule).filter_by(module_code=row["module_code"]).first()
        if existing:
                if k in row:
                    setattr(existing, k, bool(int(row[k])) if k == "is_active" else (
                        RiskLevel(row[k]) if k == "risk_level" else row[k]
                    ))
            continue
        module = RiskModule(
            module_code=row["module_code"],
            module_name=row["module_name"],
            risk_level=RiskLevel(row["risk_level"]),
            description=row.get("description", ""),
            is_active=bool(int(row.get("is_active", 1))),
        )
        session.add(module)
        logger.info(f"导入风险模块: {module.module_code}")
    session.commit()


def import_test_items(session):
    rows = read_csv("test_items_seed.csv")
    if not rows:
        return
    for row in rows:
        existing = session.query(TestItem).filter_by(test_code=row["test_code"]).first()
        if existing:
            # 已有记录，更新 module_id / is_required
            module_code = row.get("module_code", "")
            if module_code:
                mod = session.query(RiskModule).filter_by(module_code=module_code).first()
                if mod and existing.module_id is None:
                    existing.module_id = mod.id
            existing.is_required = bool(int(row.get("is_required", 0)))
            continue
        module_code = row.get("module_code", "")
        module = session.query(RiskModule).filter_by(module_code=module_code).first()
        if not module:
            logger.warning(f"模块 {module_code} 不存在，跳过测试项 {row['test_code']}")
            continue
        item = TestItem(
            test_code=row["test_code"],
            test_name=row["test_name"],
            module_id=module.id,
            default_risk_level=RiskLevel(row.get("default_risk_level", "MEDIUM")),
            is_required=bool(int(row.get("is_required", 0))),
            description=row.get("description", ""),
        )
        session.add(item)
        logger.info(f"导入测试项: {item.test_code} -> {module_code}")
    session.commit()


def import_module_test_maps(session):
    rows = read_csv("module_test_map_seed.csv")
    if not rows:
        return
    for row in rows:
        existing = session.query(ModuleTestMap).filter_by(
            module_code=row["module_code"],
            test_code=row["test_code"],
        ).first()
        if existing:
                if k in row:
                    val = row[k]
                    if k == "is_active" or k == "is_required":
                        val = bool(int(val))
                    setattr(existing, k, val)
            continue
        mp = ModuleTestMap(
            module_code=row["module_code"],
            test_code=row["test_code"],
            is_required=bool(int(row.get("is_required", 0))),
            remark=row.get("remark", ""),
            is_active=bool(int(row.get("is_active", 1))),
        )
        session.add(mp)
        logger.info(f"导入映射: {mp.module_code} -> {mp.test_code}")
    session.commit()


def run():
    logger.info("开始导入种子数据...")
    session = Session()
    try:
        import_users(session)
        import_projects(session)
        import_risk_modules(session)
        import_test_items(session)
        import_module_test_maps(session)
        logger.info("种子数据导入完成!")
    except Exception as e:
        session.rollback()
        logger.error(f"导入失败: {e}", exc_info=True)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run()
