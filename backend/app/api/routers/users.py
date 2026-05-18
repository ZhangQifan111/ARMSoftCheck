from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.models import User, UserRole
from app.schemas.schemas import UserCreate, UserUpdate, UserOut, PageResponse
from app.api.deps import get_current_user, require_admin
from app.services.log_service import write_log

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=PageResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    role: Optional[UserRole] = None,
    status: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = select(User)
    if keyword:
        query = query.where(
            (User.username.contains(keyword)) | (User.real_name.contains(keyword)) | (User.email.contains(keyword))
        )
    if role:
        query = query.where(User.role == role)
    if status is not None:
        query = query.where(User.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(User.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [UserOut.model_validate(u) for u in result.scalars().all()]
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # 检查重复
    existing = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

    user = User(
        username=body.username,
        hashed_password=get_password_hash(body.password),
        real_name=body.real_name,
        email=body.email,
        role=body.role,
        status=body.status,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await write_log(
        db, current_user.id, current_user.real_name,
        "USER", "CREATE", business_id=user.id,
        detail=f"创建用户 {user.username}({user.role.value})"
    )

    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if body.email and body.email != user.email:
        existing = await db.execute(select(User).where(User.email == body.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="邮箱已被使用")

    update_data = body.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for k, v in update_data.items():
        setattr(user, k, v)

    await db.commit()
    await db.refresh(user)

    await write_log(
        db, current_user.id, current_user.real_name,
        "USER", "UPDATE", business_id=user.id,
        detail=f"更新用户 {user.username}"
    )

    return UserOut.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "USER", "DELETE", business_id=user_id,
        detail=f"删除用户 {user.username}"
    )

    return {"code": 0, "message": "删除成功"}
