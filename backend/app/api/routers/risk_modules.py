from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional
from app.core.database import get_db
from app.models.models import RiskModule, User
from app.schemas.schemas import RiskModuleCreate, RiskModuleUpdate, RiskModuleOut, PageResponse
from app.api.deps import get_current_user, require_admin
from app.services.log_service import write_log

router = APIRouter(prefix="/risk-modules", tags=["风险模块管理"])


@router.get("", response_model=PageResponse)
async def list_risk_modules(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    keyword: Optional[str] = None,
    risk_level: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(RiskModule)
    if keyword:
        query = query.where(
            (RiskModule.module_code.contains(keyword)) | (RiskModule.module_name.contains(keyword))
        )
    if risk_level:
        query = query.where(RiskModule.risk_level == risk_level)
    if is_active is not None:
        query = query.where(RiskModule.is_active == is_active)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.order_by(RiskModule.sort_order, RiskModule.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [RiskModuleOut.model_validate(m) for m in result.scalars().all()]
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("", response_model=RiskModuleOut, status_code=201)
async def create_risk_module(
    body: RiskModuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = await db.execute(
        select(RiskModule).where(RiskModule.module_code == body.module_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="模块代码已存在")

    module = RiskModule(**body.model_dump())
    db.add(module)
    await db.commit()
    await db.refresh(module)

    await write_log(
        db, current_user.id, current_user.real_name,
        "RISK_MODULE", "CREATE", business_id=module.id,
        detail=f"创建风险模块 {module.module_code}({module.module_name})"
    )

    return RiskModuleOut.model_validate(module)


@router.put("/{module_id}", response_model=RiskModuleOut)
async def update_risk_module(
    module_id: int,
    body: RiskModuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(RiskModule).where(RiskModule.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(module, k, v)

    await db.commit()
    await db.refresh(module)

    await write_log(
        db, current_user.id, current_user.real_name,
        "RISK_MODULE", "UPDATE", business_id=module_id,
        detail=f"更新风险模块 {module.module_code}"
    )

    return RiskModuleOut.model_validate(module)


@router.delete("/{module_id}")
async def delete_risk_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(RiskModule).where(RiskModule.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    await db.execute(delete(RiskModule).where(RiskModule.id == module_id))
    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "RISK_MODULE", "DELETE", business_id=module_id,
        detail=f"删除风险模块 {module.module_code}"
    )

    return {"code": 0, "message": "删除成功"}
