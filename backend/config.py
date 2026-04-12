"""
统一配置层 — 唯一配置入口
所有敏感配置集中在此，禁止在其他文件中硬编码
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（项目根目录和 backend 目录均可）
_project_root = Path(__file__).parent.parent
_backend_dir = Path(__file__).parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_project_root / ".env")
load_dotenv(_project_root / "backend" / ".env")


class Settings:
    """统一配置类"""

    # ===== 数据库 =====
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://kis@localhost:5432/budget_system"
    )

    # ===== DeepSeek（LLM 语义解析）=====
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv(
        "DEEPSEEK_API_BASE", "https://api.deepseek.com"
    )
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ===== SiliconFlow（向量嵌入）=====
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "")
    SILICONFLOW_EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"

    # ===== MiniMax（已废弃，统一使用 DeepSeek）=====
    MINIMAX_API_KEY: str = os.getenv("MINIMAX_API_KEY", "")
    MINIMAX_API_BASE: str = os.getenv(
        "MINIMAX_API_BASE", "https://api.minimax.chat"
    )

    # ===== API 版本 =====
    API_V1_PREFIX: str = "/api/v1"

    # ===== JWT 认证 =====
    JWT_SECRET: str = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
    JWT_ALGORITHM: str = "HS256"


# 全局单例
settings = Settings()
