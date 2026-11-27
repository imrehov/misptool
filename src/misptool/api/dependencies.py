from collections.abc import Iterator
from functools import lru_cache
import os

from fastapi import Depends, HTTPException, Request

from src.misptool.application.ports import EventStateRepository
from src.misptool.infrastructure.db.repositories import PostgresEventStateRepository
from src.misptool.infrastructure.db.session import DbSession
from src.misptool.config import Config
from src.misptool.application.auth_service import AuthService, InvalidCredentials
from src.misptool.infrastructure.db.auth_repository import AuthRepository


SESSION_COOKIE = "misptool_session"


@lru_cache
def get_db() -> DbSession:
    return DbSession()


def get_auth_repo() -> Iterator[AuthRepository]:
    with get_db().session() as session:
        yield AuthRepository(session)


def get_auth_service(repo: AuthRepository = Depends(get_auth_repo)) -> AuthService:
    return AuthService(repo)


def require_session(request: Request, auth: AuthService = Depends(get_auth_service)) -> None:
    try:
        auth.require_session(request.cookies.get(SESSION_COOKIE))
    except InvalidCredentials:
        raise HTTPException(401, "Authentication required") from None


def allowed_origins() -> list[str]:
    return [origin.strip() for origin in os.environ.get(
        "AUTH_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080",
    ).split(",") if origin.strip()]


def cookie_secure() -> bool:
    return os.environ.get("AUTH_COOKIE_SECURE", "true").lower() != "false"


def require_auth_post(request: Request) -> None:
    # A custom header prevents cross-site HTML forms; CORS permits only configured origins.
    if request.headers.get("X-CSRF-Protection") != "1":
        raise HTTPException(403, "Missing CSRF protection header")
    origin = request.headers.get("origin")
    if origin is not None and origin not in allowed_origins():
        raise HTTPException(403, "Origin not allowed")


def get_event_state_repo() -> Iterator[EventStateRepository]:
    db = get_db()

    with db.session() as session:
        yield PostgresEventStateRepository(session)

def get_config() -> Config:
    return Config("config.yaml")
