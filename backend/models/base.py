"""
所有 SQLAlchemy 模型的基类
从此文件导入 Base，所有模型和 database.py 都依赖此文件
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
