from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import OperationLog, User
from datetime import datetime, timezone


async def write_log(
    db: AsyncSession,
    operator_id: int,
    operator_name: str,
    business_type: str,
    action: str,
    business_id: int = None,
    business_no: str = None,
    detail: str = None,
    ip_address: str = None,
):
    log = OperationLog(
        operator_id=operator_id,
        operator_name=operator_name,
        business_type=business_type,
        action=action,
        business_id=business_id,
        business_no=business_no,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(log)
    await db.commit()
