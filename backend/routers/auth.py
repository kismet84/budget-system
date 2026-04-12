"""
认证路由：登录获取 JWT 令牌
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["认证"])

# 演示用户（实际项目应从数据库读取）
# 用户名: admin  密码: admin123
DEMO_USERS = {
    "admin": {
        "password": hash_password("admin123"),
        "role": "admin",
        "name": "管理员",
    },
    "viewer": {
        "password": hash_password("viewer123"),
        "role": "viewer",
        "name": "访客",
    },
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """用户名密码登录，返回 JWT 令牌"""
    user = DEMO_USERS.get(body.username)
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    token = create_access_token({
        "sub": body.username,
        "role": user["role"],
        "name": user["name"],
    })
    return LoginResponse(
        access_token=token,
        role=user["role"],
        name=user["name"],
    )
