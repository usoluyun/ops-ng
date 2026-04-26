"""
用户注册路由
提供用户注册功能
"""
from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from schemas.user import RegisterRequest, RegisterResponse, UserResponse
from services.strapi_client import create_user, check_email_exists
from core.security import is_password_strong

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request, error: str = None):
    """
    渲染注册表单页面

    Args:
        request: FastAPI 请求对象
        error: 错误信息（可选）
    """
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": error},
    )


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(...),
):
    """
    处理用户注册提交

    Args:
        request: FastAPI 请求对象
        email: 邮箱
        password: 密码
        username: 用户名
    """
    # 验证密码强度
    if not is_password_strong(password):
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "email": email,
                "username": username,
                "error": "密码强度不足：需包含大小写字母、数字和特殊字符",
            },
            status_code=400,
        )

    # 检查邮箱是否已存在
    if await check_email_exists(email):
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "email": email,
                "username": username,
                "error": "该邮箱已被注册",
            },
            status_code=400,
        )

    # 创建用户
    user = await create_user(email, password, username)
    if user is None:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "email": email,
                "username": username,
                "error": "注册失败，请稍后重试",
            },
            status_code=500,
        )

    # 注册成功，返回成功消息（实际应该跳转到登录页）
    return templates.TemplateResponse(
        "register_success.html",
        {
            "request": request,
            "email": email,
            "message": "注册成功，请登录",
        },
    )


@router.api_route("/api/register", methods=["GET", "POST"])
async def api_register(request: Request):
    """
    API 格式的注册接口（返回 JSON）

    支持 POST /api/register with JSON body
    """
    if request.method == "GET":
        return JSONResponse(
            content={"message": "User registration endpoint"},
        )

    # POST 处理
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON body", "code": "INVALID_BODY"},
        )

    # 验证输入
    try:
        data = RegisterRequest(**body)
    except ValidationError as e:
        errors = e.errors()
        return JSONResponse(
            status_code=400,
            content={
                "error": "Validation error",
                "code": "VALIDATION_ERROR",
                "details": errors,
            },
        )

    # 验证密码强度
    if not is_password_strong(data.password):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Password too weak",
                "code": "WEAK_PASSWORD",
                "message": "Password must contain uppercase, lowercase, digits and special characters",
            },
        )

    # 检查邮箱是否已存在
    if await check_email_exists(data.email):
        return JSONResponse(
            status_code=409,
            content={
                "error": "Email already registered",
                "code": "EMAIL_EXISTS",
            },
        )

    # 创建用户
    user = await create_user(data.email, data.password, data.username)
    if user is None:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Registration failed",
                "code": "REGISTRATION_FAILED",
            },
        )

    return JSONResponse(
        status_code=201,
        content=RegisterResponse(
            success=True,
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                username=user["username"],
            ),
            message="Registration successful",
        ).model_dump(),
    )
