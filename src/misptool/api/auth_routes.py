from fastapi import APIRouter, Depends, HTTPException, Request, Response

from src.misptool.api.dependencies import (
    SESSION_COOKIE, cookie_secure, get_auth_service, require_auth_post, require_session,
)
from src.misptool.api.schemas import LoginRequest
from src.misptool.application.auth_service import (
    AuthService, InvalidCredentials, SESSION_SECONDS, TooManyAttempts,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", status_code=204, dependencies=[Depends(require_auth_post)])
def login(data: LoginRequest, request: Request,
          auth: AuthService = Depends(get_auth_service)) -> Response:
    try:
        token = auth.login(data.password.get_secret_value(), request.cookies.get(SESSION_COOKIE))
    except InvalidCredentials:
        raise HTTPException(401, "Invalid password or access unavailable") from None
    except TooManyAttempts:
        raise HTTPException(429, "Too many attempts; try again later") from None
    response = Response(status_code=204)
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_SECONDS,
        httponly=True, secure=cookie_secure(), samesite="lax", path="/",
    )
    return response


@router.get("/session", status_code=204, dependencies=[Depends(require_session)])
def session_status() -> Response:
    return Response(status_code=204)


@router.post("/logout", status_code=204, dependencies=[Depends(require_auth_post)])
def logout(request: Request, auth: AuthService = Depends(get_auth_service)) -> Response:
    auth.logout(request.cookies.get(SESSION_COOKIE))
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, path="/", secure=cookie_secure(), httponly=True, samesite="lax")
    return response
