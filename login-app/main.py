"""
ops-ng Login App
FastAPI 登录应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import login, consent, register

app = FastAPI(
    title="ops-ng Login App",
    description="Login and Consent handling for ops-ng SSO",
    version="1.0.0",
)

# 模板配置
templates = Jinja2Templates(directory="templates")

# 注册路由
app.include_router(login.router)
app.include_router(consent.router)
app.include_router(register.router)


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "login-app"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "ops-ng Login App",
        "version": "1.0.0",
        "docs": "/docs",
    }
