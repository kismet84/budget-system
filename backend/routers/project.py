"""
项目预算路由
提供项目的 CRUD 操作、定额管理、预算书导出
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List

from database import get_db
from models.project import Project
from models.project_quota import ProjectQuota
from models.quota import Quota
from schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectDetailResponse, ProjectQuotaAdd, ProjectQuotaItem,
)
from core.security import get_current_user, require_role

router = APIRouter(prefix="/projects", tags=["项目管理"])


def _project_summary(db: Session, project_id: int) -> dict:
    """计算项目统计信息"""
    count = db.query(func.count(ProjectQuota.id)).filter(
        ProjectQuota.project_id == project_id
    ).scalar() or 0

    result = db.execute(
        text("""
            SELECT COALESCE(SUM(q.total_cost * pq.quantity), 0) AS total
            FROM project_quotas pq
            JOIN quotas q ON q.quota_id = pq.quota_id
            WHERE pq.project_id = :pid
        """),
        {"pid": project_id}
    ).fetchone()
    total = float(result[0]) if result else 0.0

    return {"quota_count": count, "total_cost": round(total, 2)}


# ===== 项目 CRUD =====

@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """创建新项目"""
    db_proj = Project(**project.model_dump())
    db.add(db_proj)
    db.commit()
    db.refresh(db_proj)

    resp = ProjectResponse(
        **db_proj.__dict__,
        quota_count=0,
        total_cost=0.0,
    )
    return resp


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
):
    """获取项目列表"""
    q = db.query(Project)
    if status:
        q = q.filter(Project.status == status)
    projects = q.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for p in projects:
        summary = _project_summary(db, p.id)
        result.append(ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            region=p.region,
            budget_period=p.budget_period,
            notes=p.notes,
            status=p.status,
            created_by=p.created_by,
            created_at=p.created_at,
            updated_at=p.updated_at,
            quota_count=summary["quota_count"],
            total_cost=summary["total_cost"],
        ))
    return result


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """获取项目详情（含定额列表）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 取定额列表
    rows = db.execute(
        text("""
            SELECT
                q.quota_id,
                q.project_name,
                q.section,
                q.unit,
                q.total_cost,
                q.labor_fee,
                q.material_fee,
                q.machinery_fee,
                q.management_fee,
                q.tax,
                pq.quantity
            FROM project_quotas pq
            JOIN quotas q ON q.quota_id = pq.quota_id
            WHERE pq.project_id = :pid
            ORDER BY pq.id
        """),
        {"pid": project_id}
    ).fetchall()

    items = []
    for r in rows:
        items.append(ProjectQuotaItem(
            quota_id=r[0],
            project_name=r[1],
            section=r[2],
            unit=r[3],
            quantity=r[10],
            total_cost=r[4],
            labor_fee=r[5],
            material_fee=r[6],
            machinery_fee=r[7],
            management_fee=r[8],
            tax=r[9],
        ))

    summary = _project_summary(db, project_id)
    return ProjectDetailResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        region=project.region,
        budget_period=project.budget_period,
        notes=project.notes,
        status=project.status,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        quota_count=summary["quota_count"],
        total_cost=summary["total_cost"],
        items=items,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    updates: ProjectUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """更新项目信息"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)

    summary = _project_summary(db, project_id)
    return ProjectResponse(
        **project.__dict__,
        quota_count=summary["quota_count"],
        total_cost=summary["total_cost"],
    )


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """删除项目（级联删除关联定额）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return {"message": "项目已删除"}


# ===== 项目定额管理 =====

@router.post("/{project_id}/quotas", response_model=ProjectQuotaItem)
def add_quota_to_project(
    project_id: int,
    item: ProjectQuotaAdd,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """向项目添加定额"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    quota = db.query(Quota).filter(Quota.quota_id == item.quota_id).first()
    if not quota:
        raise HTTPException(status_code=404, detail=f"定额 {item.quota_id} 不存在")

    # 检查是否已存在，存在则更新数量
    existing = db.query(ProjectQuota).filter(
        ProjectQuota.project_id == project_id,
        ProjectQuota.quota_id == item.quota_id,
    ).first()

    if existing:
        existing.quantity = item.quantity
        db.commit()
        pq = existing
    else:
        pq = ProjectQuota(project_id=project_id, quota_id=item.quota_id, quantity=item.quantity)
        db.add(pq)
        db.commit()
        db.refresh(pq)

    return ProjectQuotaItem(
        quota_id=quota.quota_id,
        project_name=quota.project_name,
        section=quota.section,
        unit=quota.unit,
        quantity=pq.quantity,
        total_cost=quota.total_cost or 0,
        labor_fee=quota.labor_fee,
        material_fee=quota.material_fee,
        machinery_fee=quota.machinery_fee,
        management_fee=quota.management_fee,
        tax=quota.tax,
    )


@router.delete("/{project_id}/quotas/{quota_id}")
def remove_quota_from_project(
    project_id: int,
    quota_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """从项目移除定额"""
    row = db.query(ProjectQuota).filter(
        ProjectQuota.project_id == project_id,
        ProjectQuota.quota_id == quota_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="该项目下定额不存在")
    db.delete(row)
    db.commit()
    return {"message": "已移除"}


@router.patch("/{project_id}/quotas/{quota_id}")
def update_quota_quantity(
    project_id: int,
    quota_id: str,
    quantity: float,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """更新项目中某定额的数量"""
    row = db.query(ProjectQuota).filter(
        ProjectQuota.project_id == project_id,
        ProjectQuota.quota_id == quota_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="该项目下定额不存在")
    row.quantity = quantity
    db.commit()
    return {"quota_id": quota_id, "quantity": quantity}
