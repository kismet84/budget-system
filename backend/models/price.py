"""
信息价（材料市场价）数据模型
用于管理材料的市场参考价格，支持双轨制：
  - 信息价：官方发布的指导价
  - 企业价：企业自主采集的实际采购价
"""
from sqlalchemy import Column, String, Float, Integer, Date, Boolean
from models.base import Base


class MaterialPrice(Base):
    """材料信息价模型"""
    __tablename__ = "material_prices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)              # 材料名称
    specification = Column(String, default="")     # 规格型号
    unit = Column(String)                          # 计量单位
    unit_price = Column(Float, index=True)         # 单价（元）
    price_type = Column(String, default="信息价")    # 价格类型：信息价 / 企业价
    region = Column(String, default="武汉市")       # 地区
    publication_date = Column(Date, index=True)     # 发布日期
    source = Column(String, default="")             # 来源
    is_active = Column(Boolean, default=True)      # 是否有效（过期数据可禁用）
    remarks = Column(String, default="")            # 备注

    def __repr__(self):
        return f"<MaterialPrice({self.name}, {self.specification}, {self.unit_price})>"
