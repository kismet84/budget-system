"""
数据库连接层
统一由 config.py 提供 DATABASE_URL
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from config import settings

connect_args = {}
_db_url = settings.DATABASE_URL
if _db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # 检测 localhost/127.0.0.1 → 改用 Unix socket（绕过 Postgres.app IPv6/trust 问题）
    from urllib.parse import urlparse
    parsed = urlparse(_db_url)
    if parsed.hostname in (None, "localhost", "127.0.0.1"):
        _db_url = (
            f"postgresql://{parsed.username or 'kis'}@"
            f"/{parsed.path.lstrip('/')}"
            f"?host=/tmp"
        )

engine = create_engine(
    _db_url,
    connect_args=connect_args,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
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
    from models.project import Project            # noqa
    from models.project_quota import ProjectQuota  # noqa

    # 启用 pgvector 扩展（如果不存在）
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
