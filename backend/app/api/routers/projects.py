from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional
from app.core.database import get_db
from app.models.models import Project, User
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectOut, PageResponse
from app.api.deps import get_current_user, require_admin
from app.services.log_service import write_log

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.get("", response_model=PageResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Project)
    if keyword:
        query = query.where(Project.project_name.contains(keyword))
    if is_active is not None:
        query = query.where(Project.is_active == is_active)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.order_by(Project.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [ProjectOut.model_validate(p) for p in result.scalars().all()]
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = await db.execute(
        select(Project).where(Project.project_name == body.project_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="项目名称已存在")

    project = Project(**body.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)

    await write_log(
        db, current_user.id, current_user.real_name,
        "PROJECT", "CREATE", business_id=project.id,
        detail=f"创建项目 {project.project_name}"
    )

    return ProjectOut.model_validate(project)


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(project, k, v)

    await db.commit()
    await db.refresh(project)

    await write_log(
        db, current_user.id, current_user.real_name,
        "PROJECT", "UPDATE", business_id=project_id,
        detail=f"更新项目 {project.project_name}"
    )

    return ProjectOut.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    await db.execute(delete(Project).where(Project.id == project_id))
    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "PROJECT", "DELETE", business_id=project_id,
        detail=f"删除项目 {project.project_name}"
    )

    return {"code": 0, "message": "删除成功"}
