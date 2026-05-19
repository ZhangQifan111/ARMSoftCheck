from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.models import (
    Checklist, ChecklistModule, ChecklistTestResult, ChecklistReview,
    ChecklistStatus, RiskLevel, TestLevel, RiskModule, TestItem,
    ChangeType, User, UserRole, Project
)
from app.schemas.schemas import (
    ChecklistCreate, ChecklistUpdate, ChecklistOut, ChecklistDetailOut,
    ChecklistModuleSelect, ChecklistTestResultsUpdate, GenerateTestItemsRequest,
    GenerateTestItemOut, ReviewRequest, PageResponse,
    ChecklistTestResultDetailOut, ReviewRecordOut, RiskModuleOut, TestItemOut, ProjectOut, UserOut
)
from app.api.deps import get_current_user, require_admin
from app.services.log_service import write_log
from app.services.checklist_service import (
    generate_checklist_no, calculate_risk_level,
    get_test_items_for_modules, validate_checklist_submit
)
from fastapi import Body

router = APIRouter(prefix="/checklists", tags=["自检单"])


def _checklist_to_detail(checklist: Checklist) -> ChecklistDetailOut:
    return ChecklistDetailOut(
        id=checklist.id,
        checklist_no=checklist.checklist_no,
        title=checklist.title,
        project_id=checklist.project_id,
        product_model=checklist.product_model,
        version_no=checklist.version_no,
        branch_name=checklist.branch_name,
        commit_id=checklist.commit_id,
        mr_pr_link=checklist.mr_pr_link,
        requirement_no=checklist.requirement_no,
        change_type=checklist.change_type,
        change_summary=checklist.change_summary,
        risk_description=checklist.risk_description,
        risk_level=checklist.risk_level,
        status=checklist.status,
        creator_id=checklist.creator_id,
        reviewer_id=checklist.reviewer_id,
        review_comment=checklist.review_comment,
        review_time=checklist.review_time,
        created_at=checklist.created_at,
        updated_at=checklist.updated_at,
        submitted_at=checklist.submitted_at,
        selected_modules=[RiskModuleOut.model_validate(m.module) for m in checklist.selected_modules],
        test_results=[ChecklistTestResultDetailOut(
            id=tr.id,
            test_item_id=tr.test_item_id,
            module_id=tr.module_id,
            is_required=tr.is_required,
            test_level=tr.test_level,
            source_modules=tr.source_modules,
            executed=tr.executed,
            result=tr.result,
            remark=tr.remark,
            created_at=tr.created_at,
            updated_at=tr.updated_at,
            test_item=TestItemOut.model_validate(tr.test_item),
            module=RiskModuleOut.model_validate(tr.module),
        ) for tr in checklist.test_results],
        creator=UserOut.model_validate(checklist.creator),
        reviewer=UserOut.model_validate(checklist.reviewer) if checklist.reviewer else None,
        project=ProjectOut.model_validate(checklist.project),
    )


@router.get("", response_model=PageResponse)
async def list_checklists(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ChecklistStatus] = None,
    risk_level: Optional[RiskLevel] = None,
    project_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Checklist).options(
        selectinload(Checklist.creator),
        selectinload(Checklist.reviewer),
        selectinload(Checklist.project),
    )

    # 权限过滤
    if current_user.role == UserRole.DEVELOPER:
        query = query.where(Checklist.creator_id == current_user.id)
    elif current_user.role == UserRole.TESTER:
        query = query.where(Checklist.status.in_([ChecklistStatus.SUBMITTED, ChecklistStatus.APPROVED]))

    if status:
        query = query.where(Checklist.status == status)
    if risk_level:
        query = query.where(Checklist.risk_level == risk_level)
    if project_id:
        query = query.where(Checklist.project_id == project_id)
    if keyword:
        query = query.where(
            (Checklist.title.contains(keyword)) |
            (Checklist.checklist_no.contains(keyword)) |
            (Checklist.change_summary.contains(keyword))
        )
    if date_from:
        query = query.where(Checklist.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(Checklist.created_at <= datetime.fromisoformat(date_to))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.order_by(Checklist.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [ChecklistOut.model_validate(c) for c in result.scalars().all()]
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("", response_model=ChecklistDetailOut, status_code=201)
async def create_checklist(
    body: ChecklistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.DEVELOPER]:
        raise HTTPException(status_code=403, detail="权限不足")

    # 验证项目存在
    proj = (await db.execute(select(Project).where(Project.id == body.project_id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=400, detail="项目不存在")

    checklist = Checklist(
        **body.model_dump(),
        creator_id=current_user.id,
        status=ChecklistStatus.DRAFT,
        risk_level=RiskLevel.LOW,
    )
    db.add(checklist)
    await db.commit()
    await db.refresh(checklist)

    await write_log(
        db, current_user.id, current_user.real_name,
        "CHECKLIST", "CREATE", business_id=checklist.id,
        detail=f"创建自检单 {body.title}"
    )

    # 重新加载完整关系
    result = await db.execute(
        select(Checklist)
        .options(
            selectinload(Checklist.creator),
            selectinload(Checklist.reviewer),
            selectinload(Checklist.project),
            selectinload(Checklist.selected_modules).selectinload(ChecklistModule.module),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.test_item),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.module),
        )
        .where(Checklist.id == checklist.id)
    )
    checklist = result.scalar_one()
    return _checklist_to_detail(checklist)


@router.get("/{checklist_id}", response_model=ChecklistDetailOut)
async def get_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Checklist)
        .options(
            selectinload(Checklist.creator),
            selectinload(Checklist.reviewer),
            selectinload(Checklist.project),
            selectinload(Checklist.selected_modules).selectinload(ChecklistModule.module),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.test_item),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.module),
        )
        .where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="自检单不存在")

    # 权限检查
    if current_user.role == UserRole.DEVELOPER and checklist.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此自检单")

    return _checklist_to_detail(checklist)


@router.put("/{checklist_id}", response_model=ChecklistDetailOut)
async def update_checklist(
    checklist_id: int,
    body: ChecklistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Checklist)
        .options(
            selectinload(Checklist.creator),
            selectinload(Checklist.reviewer),
            selectinload(Checklist.project),
            selectinload(Checklist.selected_modules).selectinload(ChecklistModule.module),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.test_item),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.module),
        )
        .where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="自检单不存在")

    if checklist.status not in [ChecklistStatus.DRAFT, ChecklistStatus.RETURNED]:
        raise HTTPException(status_code=400, detail=f"当前状态不允许编辑")

    if current_user.role == UserRole.DEVELOPER and checklist.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权编辑此自检单")

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(checklist, k, v)

    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "CHECKLIST", "UPDATE", business_id=checklist_id,
        detail=f"更新自检单 {checklist.checklist_no or checklist.title}"
    )

    # 重新加载完整关系
    result = await db.execute(
        select(Checklist)
        .options(
            selectinload(Checklist.creator),
            selectinload(Checklist.reviewer),
            selectinload(Checklist.project),
            selectinload(Checklist.selected_modules).selectinload(ChecklistModule.module),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.test_item),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.module),
        )
        .where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one()
    return _checklist_to_detail(checklist)


@router.delete("/{checklist_id}")
async def delete_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="自检单不存在")

    if checklist.status != ChecklistStatus.DRAFT:
        raise HTTPException(status_code=400, detail="只能删除草稿状态的自检单")

    if current_user.role == UserRole.DEVELOPER and checklist.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此自检单")

    no = checklist.checklist_no or checklist.title
    await db.execute(delete(Checklist).where(Checklist.id == checklist_id))
    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "CHECKLIST", "DELETE", business_id=checklist_id,
        detail=f"删除自检单 {no}"
    )

    return {"code": 0, "message": "删除成功"}


@router.post("/generate-test-items", response_model=list[GenerateTestItemOut])
async def generate_test_items_api(
    body: GenerateTestItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据选中模块生成测试项（不保存，仅预览）"""
    test_items = await get_test_items_for_modules(db, body.module_ids)

    result = []
    for item in test_items:
        src = item["source_modules"][0]
        result.append(GenerateTestItemOut(
            test_item_id=item["test_item_id"],
            test_name=item["test_name"],
            module_id=src["module_id"],
            module_name=src["module_name"],
            module_code=src["module_code"],
            is_required=item["is_required"],
            test_level=TestLevel.REQUIRED if item["is_required"] else TestLevel.RECOMMENDED,
            description=item.get("description"),
        ))

    return result


@router.post("/{checklist_id}/select-modules")
async def select_modules(
    checklist_id: int,
    body: ChecklistModuleSelect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为自检单选择模块，同时生成测试项"""
    result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="自检单不存在")

    if checklist.status not in [ChecklistStatus.DRAFT, ChecklistStatus.RETURNED]:
        raise HTTPException(status_code=400, detail=f"当前状态不允许修改模块")

    if current_user.role == UserRole.DEVELOPER and checklist.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改")

    # 查询模块
    modules_result = await db.execute(
        select(RiskModule).where(RiskModule.id.in_(body.module_ids), RiskModule.is_active == True)
    )
    modules = list(modules_result.scalars().all())
    if not modules:
        raise HTTPException(status_code=400, detail="请至少选择一个有效模块")

    # 删除旧模块关联
    await db.execute(
        delete(ChecklistModule).where(ChecklistModule.checklist_id == checklist_id)
    )
    await db.flush()

    # 删除旧测试结果
    await db.execute(
        delete(ChecklistTestResult).where(ChecklistTestResult.checklist_id == checklist_id)
    )
    await db.flush()

    # 创建新模块关联
    for mod in modules:
        cm = ChecklistModule(checklist_id=checklist_id, module_id=mod.id)
        db.add(cm)

    # 计算风险等级
    checklist.risk_level = calculate_risk_level(modules)

    # 生成测试项
    test_items = await get_test_items_for_modules(db, body.module_ids)
    for item in test_items:
        src = item["source_modules"][0]
        tr = ChecklistTestResult(
            checklist_id=checklist_id,
            test_item_id=item["test_item_id"],
            module_id=src["module_id"],
            is_required=item["is_required"],
            test_level=TestLevel.REQUIRED if item["is_required"] else TestLevel.RECOMMENDED,
            source_modules=",".join([s["module_name"] for s in item["source_modules"]]),
        )
        db.add(tr)

    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "CHECKLIST", "UPDATE", business_id=checklist_id,
        detail=f"选择模块并生成测试项，共 {len(test_items)} 项"
    )

    return {"code": 0, "message": f"已生成 {len(test_items)} 个测试项"}


@router.put("/{checklist_id}/test-results", response_model=ChecklistDetailOut)
async def update_test_results(
    checklist_id: int,
    body: ChecklistTestResultsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="自检单不存在")

    if checklist.status not in [ChecklistStatus.DRAFT, ChecklistStatus.RETURNED]:
        raise HTTPException(status_code=400, detail=f"当前状态不允许填写测试结果")

    if current_user.role == UserRole.DEVELOPER and checklist.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改")

    # 更新测试结果
    for r in body.results:
        tr_result = await db.execute(
            select(ChecklistTestResult).where(ChecklistTestResult.id == r.test_result_id)
        )
        tr = tr_result.scalar_one_or_none()
        if tr and tr.checklist_id == checklist_id:
            if r.executed is not None:
                tr.executed = r.executed
            if r.result is not None:
                tr.result = r.result
            if r.remark is not None:
                tr.remark = r.remark
            await db.flush()

    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "CHECKLIST", "UPDATE", business_id=checklist_id,
        detail=f"更新测试结果"
    )

    # 重新加载
    result = await db.execute(
        select(Checklist)
        .options(
            selectinload(Checklist.creator),
            selectinload(Checklist.reviewer),
            selectinload(Checklist.project),
            selectinload(Checklist.selected_modules).selectinload(ChecklistModule.module),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.test_item),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.module),
        )
        .where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one()
    return _checklist_to_detail(checklist)


@router.post("/{checklist_id}/submit", response_model=ChecklistDetailOut)
async def submit_checklist(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Checklist)
        .options(
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.test_item),
        )
        .where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="自检单不存在")

    if checklist.status not in [ChecklistStatus.DRAFT, ChecklistStatus.RETURNED]:
        raise HTTPException(status_code=400, detail=f"当前状态不允许提交")

    if current_user.role == UserRole.DEVELOPER and checklist.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权提交")

    # 校验
    ok, msg = await validate_checklist_submit(db, checklist_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # 生成编号
    checklist_no = await generate_checklist_no(db)
    checklist.checklist_no = checklist_no
    checklist.status = ChecklistStatus.SUBMITTED
    checklist.submitted_at = datetime.now(timezone.utc)

    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "CHECKLIST", "SUBMIT", business_id=checklist_id, business_no=checklist_no,
        detail=f"提交自检单 {checklist_no}"
    )

    # 重新加载完整关系
    result = await db.execute(
        select(Checklist)
        .options(
            selectinload(Checklist.creator),
            selectinload(Checklist.reviewer),
            selectinload(Checklist.project),
            selectinload(Checklist.selected_modules).selectinload(ChecklistModule.module),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.test_item),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.module),
        )
        .where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one()
    return _checklist_to_detail(checklist)


@router.post("/{checklist_id}/review", response_model=ChecklistDetailOut)
async def review_checklist(
    checklist_id: int,
    body: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.REVIEWER]:
        raise HTTPException(status_code=403, detail="权限不足，只有评审或管理员可审核")

    result = await db.execute(
        select(Checklist).where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one_or_none()
    if not checklist:
        raise HTTPException(status_code=404, detail="自检单不存在")

    if checklist.status != ChecklistStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="只能审核已提交的自检单")

    if body.action == ChecklistStatus.APPROVED:
        checklist.status = ChecklistStatus.APPROVED
        action_str = "APPROVE"
    elif body.action == ChecklistStatus.RETURNED:
        checklist.status = ChecklistStatus.RETURNED
        action_str = "RETURN"
    else:
        raise HTTPException(status_code=400, detail="无效的审核动作")

    checklist.reviewer_id = current_user.id
    checklist.review_comment = body.comment
    checklist.review_time = datetime.now(timezone.utc)

    # 记录审核历史
    review_record = ChecklistReview(
        checklist_id=checklist_id,
        reviewer_id=current_user.id,
        action=body.action,
        comment=body.comment,
    )
    db.add(review_record)

    await db.commit()

    await write_log(
        db, current_user.id, current_user.real_name,
        "CHECKLIST", action_str, business_id=checklist_id, business_no=checklist.checklist_no,
        detail=f"审核 {checklist.checklist_no}，动作: {body.action.value}，意见: {body.comment}"
    )

    # 重新加载
    result = await db.execute(
        select(Checklist)
        .options(
            selectinload(Checklist.creator),
            selectinload(Checklist.reviewer),
            selectinload(Checklist.project),
            selectinload(Checklist.selected_modules).selectinload(ChecklistModule.module),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.test_item),
            selectinload(Checklist.test_results).selectinload(ChecklistTestResult.module),
        )
        .where(Checklist.id == checklist_id)
    )
    checklist = result.scalar_one()
    return _checklist_to_detail(checklist)


@router.get("/{checklist_id}/reviews", response_model=list[ReviewRecordOut])
async def get_review_records(
    checklist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChecklistReview)
        .options(selectinload(ChecklistReview.reviewer))
        .where(ChecklistReview.checklist_id == checklist_id)
        .order_by(ChecklistReview.created_at)
    )
    records = result.scalars().all()
    return [ReviewRecordOut.model_validate(r) for r in records]
