"""
项目-定额关联模型
项目中的定额条目，支持自定义数量（独立于 quotas 表的原始 quantity）
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from models.base import Base


class ProjectQuota(Base):
    """项目定额关联模型"""
    __tablename__ = "project_quotas"
    __table_args__ = (
        UniqueConstraint("project_id", "quota_id", name="uq_project_quota"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    quota_id = Column(String(32), ForeignKey("quotas.quota_id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Float, default=1.0)                        # 项目中该定额的实际数量
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ProjectQuota(project={self.project_id}, quota={self.quota_id}, qty={self.quantity})>"
