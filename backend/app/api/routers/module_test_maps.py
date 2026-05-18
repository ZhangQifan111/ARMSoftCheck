from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_
from typing import Optional
from app.core.database import get_db
from app.models.models import ModuleTestMap, RiskModule, TestItem, User
from app.schemas.schemas import (
    ModuleTestMapCreate, ModuleTestMapUpdate, ModuleTestMapOut, PageResponse,
    GenerateTestItemsRequest, GenerateTestItemOut
)
from app.api.deps import get_current_user, require_admin
from app.services.checklist_service import get_test_items_for_modules
from app.services.log_service import write_log

router = APIRouter(prefix="/module-test-maps", tags=["模块-测试项映射"])


@router.get("", response_model=PageResponse)
async def list_maps(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    module_code: Optional[str] = None,
    test_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ModuleTestMap)
    if module_code:
        query = query.where(ModuleTestMap.module_code == module_code)
    if test_code:
        query = query.where(ModuleTestMap.test_code == test_code)
    if is_active is not None:
        query = query.where(ModuleTestMap.is_active == is_active)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.order_by(ModuleTestMap.sort_order, ModuleTestMap.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [ModuleTestMapOut.model_validate(m) for m in result.scalars().all()]
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("", response_model=ModuleTestMapOut, status_code=201)
async def create_map(
    body: ModuleTestMapCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # 检查模块和测试项存在
    mod = (await db.execute(select(RiskModule).where(RiskModule.module_code == body.module_code))).scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=400, detail=f"模块 {body.module_code} 不存在")
    ti = (await db.execute(select(TestItem).where(TestItem.test_code == body.test_code))).scalar_one_or_none()
    if not ti:
        raise HTTPException(status_code=400, detail=f"测试项 {body.test_code} 不存在")

    existing = await db.execute(
        select(ModuleTestMap).where(
            and_(ModuleTestMap.module_code == body.module_code, ModuleTestMap.test_code == body.test_code)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="映射关系已存在")

    mp = ModuleTestMap(**body.model_dump())
    db.add(mp)
    await db.commit()
    await db.refresh(mp)

    await write_log(
        db, current_user.id, current_user.real_name,
        "MODULE_TEST_MAP", "CREATE", business_id=mp.id,
        detail=f"创建映射 {mp.module_code} -> {mp.test_code}"
    )

    return ModuleTestMapOut.model_validate(mp)


@router.put("/{map_id}", response_model=ModuleTestMapOut)
async def update_map(
    map_id: int,
    body: ModuleTestMapUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(ModuleTestMap).where(ModuleTestMap.id == map_id))
    mp = result.scalar_one_or_none()
    if not mp:
        raise HTTPException(status_code=404, detail="映射不存在")

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(mp, k, v)

    await db.commit()
    await db.refresh(mp)

    await write_log(
        db, current_user.id, current_user.real_name,
        "MODULE_TEST_MAP", "UPDATE", business_id=map_id,
        detail=f"更新映射 {mp.module_code} -> {mp.test_code}"
    )

    return ModuleTestMapOut.model_validate(mp)


@router.delete("/{map_id}")
async def delete_map(
    map_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(ModuleTestMap).where(ModuleTestMap.id == map_id))
    mp = result.scalar_one_or_none()
    if not mp:
        raise HTTPException(status_code=404, detail="映射不存在")

    await db.execute(delete(ModuleTestMap).where(ModuleTestMap.id == map_id))
    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "MODULE_TEST_MAP", "DELETE", business_id=map_id,
        detail=f"删除映射 {mp.module_code} -> {mp.test_code}"
    )

    return {"code": 0, "message": "删除成功"}


@router.post("/generate", response_model=list[GenerateTestItemOut])
async def generate_test_items(
    body: GenerateTestItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据选中模块生成测试项列表"""
    test_items = await get_test_items_for_modules(db, body.module_ids)

    result = []
    for item in test_items:
        src = item["source_modules"][0]
        result.append(GenerateTestItemOut(
            test_item_id=item["test_item_id"],
            test_code=item["test_code"],
            test_name=item["test_name"],
            module_id=src["module_id"],
            module_name=src["module_name"],
            module_code=src["module_code"],
            is_required=item["is_required"],
            test_level=item["default_level"],
            description=item.get("description"),
        ))

    return result
