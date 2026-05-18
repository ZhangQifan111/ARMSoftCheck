from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional
from app.core.database import get_db
from app.models.models import TestItem, User
from app.schemas.schemas import TestItemCreate, TestItemUpdate, TestItemOut, PageResponse
from app.api.deps import get_current_user, require_admin
from app.services.log_service import write_log

router = APIRouter(prefix="/test-items", tags=["测试项管理"])


@router.get("", response_model=PageResponse)
async def list_test_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(TestItem)
    if keyword:
        query = query.where(
            (TestItem.test_code.contains(keyword)) | (TestItem.test_name.contains(keyword))
        )
    if is_active is not None:
        query = query.where(TestItem.is_active == is_active)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.order_by(TestItem.sort_order, TestItem.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [TestItemOut.model_validate(t) for t in result.scalars().all()]
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("", response_model=TestItemOut, status_code=201)
async def create_test_item(
    body: TestItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = await db.execute(
        select(TestItem).where(TestItem.test_code == body.test_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="测试项代码已存在")

    item = TestItem(**body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)

    await write_log(
        db, current_user.id, current_user.real_name,
        "TEST_ITEM", "CREATE", business_id=item.id,
        detail=f"创建测试项 {item.test_code}({item.test_name})"
    )

    return TestItemOut.model_validate(item)


@router.put("/{item_id}", response_model=TestItemOut)
async def update_test_item(
    item_id: int,
    body: TestItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(TestItem).where(TestItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="测试项不存在")

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(item, k, v)

    await db.commit()
    await db.refresh(item)

    await write_log(
        db, current_user.id, current_user.real_name,
        "TEST_ITEM", "UPDATE", business_id=item_id,
        detail=f"更新测试项 {item.test_code}"
    )

    return TestItemOut.model_validate(item)


@router.delete("/{item_id}")
async def delete_test_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(TestItem).where(TestItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="测试项不存在")

    await db.execute(delete(TestItem).where(TestItem.id == item_id))
    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "TEST_ITEM", "DELETE", business_id=item_id,
        detail=f"删除测试项 {item.test_code}"
    )

    return {"code": 0, "message": "删除成功"}
