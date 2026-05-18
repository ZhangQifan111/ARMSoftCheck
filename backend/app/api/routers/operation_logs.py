from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.core.database import get_db
from app.models.models import OperationLog, User
from app.schemas.schemas import OperationLogOut, PageResponse
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/operation-logs", tags=["操作日志"])


@router.get("", response_model=PageResponse)
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    operator_id: Optional[int] = None,
    business_type: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = select(OperationLog)
    if operator_id:
        query = query.where(OperationLog.operator_id == operator_id)
    if business_type:
        query = query.where(OperationLog.business_type == business_type)
    if action:
        query = query.where(OperationLog.action == action)
    if date_from:
        from datetime import datetime
        query = query.where(OperationLog.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        from datetime import datetime
        query = query.where(OperationLog.created_at <= datetime.fromisoformat(date_to))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.order_by(OperationLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [OperationLogOut.model_validate(log) for log in result.scalars().all()]
    return PageResponse(total=total, page=page, page_size=page_size, items=items)
