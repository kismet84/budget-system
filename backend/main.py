from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import init_db
from routers import quota, search, ai_search, price, auth, quota_import, price_import, data_report


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(quota.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_search.router, prefix=settings.API_V1_PREFIX)
app.include_router(price.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router)  # /auth/login 在根路径
app.include_router(data_report.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {"message": "建设工程预算分析系统 API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
