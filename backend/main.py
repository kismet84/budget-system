from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import init_db
from routers import quota, ai_search, price, auth, quota_import, price_import, data_report


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库"""
    init_db()
    yield


app = FastAPI(
    title="建设工程预算分析系统",
    description="施工单位自用轻量级预算工具，专注投标报价估算+成本分析",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = [
    "http://localhost:5173",   # 前端开发服务器
    "http://localhost:8501",  # Streamlit（已废弃，保留兼容性）
]
# 支持以逗号分隔的环境变量配置，如：http://localhost:5173,https://staging.example.com
if os.environ.get("CORS_ORIGINS"):
    _cors_origins.extend([o.strip() for o in os.environ["CORS_ORIGINS"].split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(quota.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_search.router, prefix=settings.API_V1_PREFIX)
app.include_router(price.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router)  # /auth/login 在根路径
app.include_router(data_report.router, prefix=settings.API_V1_PREFIX)
app.include_router(price_import.router, prefix=settings.API_V1_PREFIX)
app.include_router(quota_import.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {"message": "建设工程预算分析系统 API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
