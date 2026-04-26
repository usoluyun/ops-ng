"""
登录路由
提供用户登录功能
"""
import os
from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.strapi_client import verify_credentials
from services.hydra_client import get_login_request, accept_login, reject_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, login_challenge: str = None, error: str = None):
    """
    渲染登录表单页面

    Args:
        request: FastAPI 请求对象
        login_challenge: Hydra 登录挑战（用于 OAuth2 流程）
        error: 错误信息（可选）
    """
    # 如果提供了 login_challenge，验证其有效性
    if login_challenge:
        try:
            await get_login_request(login_challenge)
        except Exception:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": "无效的登录请求，请重试",
                    "code": "INVALID_CHALLENGE",
                },
                status_code=400,
            )

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "login_challenge": login_challenge,
            "error": error,
        },
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    login_challenge: str = Form(None),
    identifier: str = Form(...),
    password: str = Form(...),
):
    """
    处理登录表单提交

    Args:
        request: FastAPI 请求对象
        login_challenge: Hydra 登录挑战（用于 OAuth2 流程）
        identifier: 用户名或邮箱
        password: 密码
    """
    # 验证凭证
    user = await verify_credentials(identifier, password)

    if user is None:
        # 凭证验证失败
        error_msg = "账号或密码错误，请重试"
        if login_challenge:
            # 在 OAuth2 流程中，返回错误页面
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "login_challenge": login_challenge,
                    "error": error_msg,
                },
                status_code=401,
            )
        else:
            # 非 OAuth2 流程，返回 JSON 错误
            return JSONResponse(
                status_code=401,
                content={"error": error_msg, "code": "INVALID_CREDENTIALS"},
            )

    # 凭证验证成功
    if login_challenge:
        # 在 OAuth2 流程中，回调 Hydra
        try:
            redirect_to = await accept_login(login_challenge, subject=user["id"])
            return RedirectResponse(redirect_to, status_code=302)
        except Exception as e:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"登录回调失败: {str(e)}",
                    "code": "HYDRA_ERROR",
                },
                status_code=500,
            )
    else:
        # 非 OAuth2 流程，返回成功 JSON
        return JSONResponse(
            content={
                "success": True,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "username": user["username"],
                },
                "token": user.get("jwt"),
            },
        )


@router.api_route("/api/login", methods=["GET", "POST"])
async def api_login(request: Request):
    """
    API 格式的登录接口（返回 JSON）

    支持 POST /api/login with JSON body
    """
    if request.method == "GET":
        return JSONResponse(
            content={"message": "User login endpoint"},
        )

    # POST 处理
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON body", "code": "INVALID_BODY"},
        )

    identifier = body.get("identifier")
    password = body.get("password")

    if not identifier or not password:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Missing identifier or password",
                "code": "MISSING_CREDENTIALS",
            },
        )

    # 验证凭证
    user = await verify_credentials(identifier, password)

    if user is None:
        return JSONResponse(
            status_code=401,
            content={
                "error": "Invalid identifier or password",
                "code": "INVALID_CREDENTIALS",
            },
        )

    return JSONResponse(
        content={
            "success": True,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
            },
            "token": user.get("jwt"),
        },
    )


@router.get("/logout")
async def logout(request: Request):
    """
    处理登出请求

    Phase 1: 简单返回成功，不做 Hydra logout 处理
    """
    return {"status": "logged out", "message": "Logout successful"}
