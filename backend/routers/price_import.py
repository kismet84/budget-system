"""
信息价 Excel 导入路由（E3-S3.1）
提供管理员端 Excel 批量导入功能
"""
import os
import uuid
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.price import MaterialPrice
from scripts.parse_info_price import parse_xlsx, get_month

router = APIRouter(prefix="/admin/price", tags=["管理员-信息价导入"])


class ImportReport(BaseModel):
    """导入报告"""
    total_rows: int           # 解析出的总行数
    imported: int             # 实际导入数据库的条数
    skipped: int              # 跳过的条数（数据无效或已存在）
    errors: list[str]         # 错误信息列表
    filename: str            # 原始文件名
    month: str               # 解析出的月份


@router.post("/import", response_model=ImportReport)
async def import_price_excel(
    file: UploadFile = File(..., description="Excel 文件（.xlsx）"),
    region: Optional[str] = Query(None, description="强制指定地区，默认从文件名/表格自动识别"),
    price_type: str = Query("信息价", description="价格类型：信息价/企业价"),
    db: Session = Depends(get_db),
):
    """
    上传 Excel 文件，解析后批量导入到 material_prices 表
    """
    # 校验文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 或 .xls 格式")

    # 保存到临时文件
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        # 解析
        month = get_month(file.filename)
        records = parse_xlsx(tmp_path, month)

        if not records:
            return ImportReport(
                total_rows=0,
                imported=0,
                skipped=0,
                errors=["未能解析出有效数据，请检查文件格式"],
                filename=file.filename,
                month=month or "未知",
            )

        # 批量入库
        imported = 0
        skipped = 0
        errors = []

        for rec in records:
            try:
                # 解析日期
                pub_date = None
                if rec.get("月份"):
                    try:
                        pub_date = datetime.strptime(rec["月份"], "%Y-%m").date()
                    except:
                        pass

                # 决定地区
                region_val = region or rec.get("城市", "武汉市")

                price = MaterialPrice(
                    name=rec.get("材料名称", "").strip(),
                    specification=rec.get("规格及型号", "").strip(),
                    unit=rec.get("单位", "").strip(),
                    unit_price=rec.get("含税价") or rec.get("除税价", 0),
                    price_type=price_type,
                    region=region_val,
                    publication_date=pub_date,
                    source="Excel导入",
                    is_active=True,
                    remarks=f"来自文件: {file.filename}",
                )
                db.add(price)
                imported += 1
            except Exception as e:
                skipped += 1
                if len(errors) < 10:  # 只保留前10条错误
                    errors.append(f"行 {imported + skipped}: {str(e)}")

        db.commit()

        return ImportReport(
            total_rows=len(records),
            imported=imported,
            skipped=skipped,
            errors=errors,
            filename=file.filename,
            month=month or "未知",
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/report", response_model=list[ImportReport])
def get_import_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    获取导入历史（从已导入的记录中按文件名/月份聚合）
    """
    # 简单实现：按 source 和 region 聚合最近导入
    results = (
        db.query(
            MaterialPrice.source,
            MaterialPrice.region,
            MaterialPrice.publication_date,
        )
        .filter(MaterialPrice.source.like("Excel导入%"))
        .order_by(MaterialPrice.publication_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # 去重聚合（实际项目中建议单独建 import_logs 表）
    seen = set()
    reports = []
    for r in results:
        key = (r.source, r.region)
        if key not in seen:
            seen.add(key)
            count = db.query(MaterialPrice).filter(
                MaterialPrice.source == r.source,
                MaterialPrice.region == r.region,
            ).count()
            reports.append(ImportReport(
                total_rows=count,
                imported=count,
                skipped=0,
                errors=[],
                filename=r.source.replace("来自文件: ", ""),
                month=str(r.publication_date)[:7] if r.publication_date else "未知",
            ))

    return reports
