"""
SQLAlchemy 数据库模型
"""
from sqlalchemy import Column, String, Float, Integer, Text, LargeBinary
from models.base import Base

# pgvector 支持（若无 pgvector 则 Vector 为空注解，降级为 LargeBinary 存储）
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None  # type: ignore


class Quota(Base):
    """定额模型"""
    __tablename__ = "quotas"

    id = Column(Integer, primary_key=True, index=True)
    quota_id = Column(String, unique=True, index=True)   # 如 "E1-1"
    category = Column(String, index=True)                # 专业类别
    unit = Column(String)                                 # 计量单位
    work_content = Column(Text)                          # 工作内容
    section = Column(String)                             # 分部工程
    total_cost = Column(Float)                           # 全费用
    labor_fee = Column(Float)                            # 人工费
    material_fee = Column(Float)                         # 材料费
    machinery_fee = Column(Float)                        # 机械费
    management_fee = Column(Float)                        # 管理费（含利润、规费）
    tax = Column(Float)                                  # 增值税
    source_file = Column(String)                          # 来源文件
    project_name = Column(String)                         # 项目名称
    embedding = Column(Vector(1024) if Vector else LargeBinary, nullable=True)  # 向量嵌入 (1024维)


class Material(Base):
    """材料明细模型"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    quota_id = Column(String, index=True)               # 关联定额编号
    name = Column(String)                                 # 材料/机械名称
    unit = Column(String)                                 # 单位
    unit_price = Column(Float)                           # 单价
    consumption = Column(Float)                          # 消耗量
    mat_type = Column(String)                            # 类型：材料 / 机械
