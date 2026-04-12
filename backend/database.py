"""
数据库连接层
统一由 config.py 提供 DATABASE_URL
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_size=5,           # 常规连接池大小
    max_overflow=10,       # 允许额外创建的连接数（峰值）
    pool_pre_ping=True,    # 每次使用前检测连接是否存活（防断开）
    pool_recycle=3600,     # 1小时回收连接（防超时）
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    from models.base import Base  # noqa
    # 导入所有模型以确保 metadata 包含所有表
    from models.quota import Quota, Material      # noqa
    from models.price import MaterialPrice        # noqa

    # 启用 pgvector 扩展（如果不存在）
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
