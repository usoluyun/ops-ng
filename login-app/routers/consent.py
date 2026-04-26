"""
Consent 路由
处理 OAuth2 Consent 流程
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from services.hydra_client import get_consent_request, accept_consent, reject_consent

router = APIRouter()


@router.get("/consent")
async def consent(request: Request, consent_challenge: str):
    """
    自动接受 Consent 流程

    Phase 1: 自动接受所有 consent 请求，不显示授权页面

    Args:
        request: FastAPI 请求对象
        consent_challenge: Hydra consent 挑战
    """
    try:
        consent_req = await get_consent_request(consent_challenge)
    except Exception as e:
        return {
            "error": f"Failed to get consent request: {str(e)}",
            "code": "HYDRA_ERROR",
        }

    subject = consent_req.get("subject", "")
    requested_scope = consent_req.get("requested_scope", [])

    if not subject:
        # 没有登录，跳转到登录页
        return RedirectResponse(
            url=f"/login?login_challenge={consent_req.get('login_challenge', '')}",
            status_code=302,
        )

    try:
        redirect_to = await accept_consent(
            challenge=consent_challenge,
            subject=subject,
            requested_scope=requested_scope,
        )
        return RedirectResponse(redirect_to, status_code=302)
    except Exception as e:
        return {
            "error": f"Failed to accept consent: {str(e)}",
            "code": "HYDRA_ERROR",
        }


@router.post("/consent/reject")
async def consent_reject(request: Request, consent_challenge: str):
    """
    拒绝 Consent 请求

    Args:
        request: FastAPI 请求对象
        consent_challenge: Hydra consent 挑战
    """
    try:
        redirect_to = await reject_consent(
            challenge=consent_challenge,
            error="access_denied",
            error_description="User denied consent",
        )
        return RedirectResponse(redirect_to, status_code=302)
    except Exception as e:
        return {
            "error": f"Failed to reject consent: {str(e)}",
            "code": "HYDRA_ERROR",
        }
