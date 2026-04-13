"""
项目数据模型
用于组织和管理预算项目，支持多项目并行
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.sql import func
from models.base import Base


class Project(Base):
    """项目模型"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)        # 项目名称
    description = Column(Text, default="")                        # 项目描述
    region = Column(String(64), default="武汉市")                  # 地区
    budget_period = Column(String(64), default="")                 # 预算编制期
    notes = Column(Text, default="")                             # 备注
    status = Column(String(32), default="进行中")                 # 项目状态：进行中/已完成/已归档
    created_by = Column(String(64), default="admin")               # 创建人
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Project({self.id}, {self.name})>"
