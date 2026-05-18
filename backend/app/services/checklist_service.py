from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import List, Tuple

from app.models.models import (
    Checklist, ChecklistSequence, ChecklistModule, ChecklistTestResult,
    RiskModule, TestItem, ModuleTestMap, ChecklistStatus, RiskLevel, TestLevel,
    ChangeType, User, Project
)
from app.services.log_service import write_log


async def generate_checklist_no(db: AsyncSession) -> str:
    """生成唯一编号 PRRC-YYYYMMDD-XXXX"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    # 使用行锁保证并发唯一
    result = await db.execute(
        select(ChecklistSequence)
        .where(ChecklistSequence.date_str == today)
        .with_for_update()
    )
    seq = result.scalar_one_or_none()

    if seq is None:
        seq = ChecklistSequence(date_str=today, current_value=0)
        db.add(seq)
        await db.flush()

    seq.current_value += 1
    serial = seq.current_value

    await db.commit()
    return f"PRRC-{today}-{serial:04d}"


def calculate_risk_level(modules: List[RiskModule]) -> RiskLevel:
    """根据选中模块计算自检单风险等级"""
    levels = {m.risk_level for m in modules}
    if RiskLevel.HIGH in levels:
        return RiskLevel.HIGH
    if RiskLevel.MEDIUM in levels:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


async def get_test_items_for_modules(
    db: AsyncSession,
    module_ids: List[int],
) -> List[dict]:
    """根据选中模块查询映射的测试项，返回合并去重后的测试项列表"""
    # 查询所有映射
    result = await db.execute(
        select(ModuleTestMap)
        .options(selectinload(ModuleTestMap.module), selectinload(ModuleTestMap.test_item))
        .where(
            ModuleTestMap.module_id.in_(module_ids),
            ModuleTestMap.is_active == True,
            ModuleTestMap.module.has(RiskModule.is_active == True),
            ModuleTestMap.test_item.has(TestItem.is_active == True),
        )
        .order_by(ModuleTestMap.sort_order)
    )
    maps = result.scalars().all()

    # 按 test_item_id 合并去重
    item_map: dict[int, dict] = {}
    for m in maps:
        tid = m.test_item_id
        if tid not in item_map:
            item_map[tid] = {
                "test_item_id": m.test_item_id,
                "test_code": m.test_item.test_code,
                "test_name": m.test_item.test_name,
                "default_level": m.test_item.default_level,
                "default_risk_level": m.test_item.default_risk_level,
                "description": m.test_item.description,
                "source_modules": [],
                "is_required": m.is_required,
            }
        else:
            # 任一映射标记为必做，则最终必做
            if m.is_required:
                item_map[tid]["is_required"] = True
        item_map[tid]["source_modules"].append({
            "module_id": m.module_id,
            "module_name": m.module.module_name,
            "module_code": m.module.module_code,
        })

    return list(item_map.values())


async def create_or_update_test_results(
    db: AsyncSession,
    checklist_id: int,
    test_items: List[dict],
):
    """为自检单创建或更新测试项记录"""
    # 删除旧测试结果记录
    await db.execute(
        delete(ChecklistTestResult)
        .where(ChecklistTestResult.checklist_id == checklist_id)
    )
    await db.flush()

    for item in test_items:
        # 取第一个来源模块
        src = item["source_modules"][0]
        tr = ChecklistTestResult(
            checklist_id=checklist_id,
            test_item_id=item["test_item_id"],
            module_id=src["module_id"],
            is_required=item["is_required"],
            test_level=item["default_level"],
            source_modules=",".join([s["module_name"] for s in item["source_modules"]]),
            executed=None,
            result=None,
            remark=None,
        )
        db.add(tr)


async def validate_checklist_submit(
    db: AsyncSession,
    checklist_id: int,
) -> Tuple[bool, str]:
    """校验自检单是否可以提交"""
    result = await db.execute(
        select(Checklist)
        .options(selectinload(Checklist.test_results))
        .where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        return False, "自检单不存在"

    if checklist.status != ChecklistStatus.DRAFT and checklist.status != ChecklistStatus.RETURNED:
        return False, f"当前状态 {checklist.status} 不允许提交"

    if not checklist.selected_modules:
        return False, "请至少选择一个改动模块"

    for tr in checklist.test_results:
        if tr.is_required:
            if tr.executed is None:
                return False, f"必做项 '{tr.test_item.test_name}' 未填写执行情况"
            if tr.executed.value in ("NO", "NA") and not tr.remark:
                return False, f"必做项 '{tr.test_item.test_name}' 未执行/不适用，请填写原因"
            if tr.executed.value == "YES" and tr.result is None:
                return False, f"必做项 '{tr.test_item.test_name}' 已执行，请填写测试结果"
            if tr.executed.value == "YES" and tr.result.value == "FAIL" and not tr.remark:
                return False, f"必做项 '{tr.test_item.test_name}' 测试失败，请填写说明"

    return True, ""
