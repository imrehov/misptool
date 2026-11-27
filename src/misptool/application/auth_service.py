import hashlib
import os
import secrets
import time

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError

from src.misptool.infrastructure.db.auth_repository import AuthRepository


PASSWORD_HASHER = PasswordHasher(type=Type.ID, time_cost=3, memory_cost=65536, parallelism=4)
SESSION_SECONDS = 8 * 60 * 60


class InvalidCredentials(Exception):
    pass


class TooManyAttempts(Exception):
    pass


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def password_hash(self) -> str:
        configured = os.environ.get("APP_PASSWORD_HASH", "")
        if not configured.startswith("$argon2id$"):
            raise InvalidCredentials
        return configured

    def login(self, password: str, previous_token: str | None) -> str:
        if not self.repo.consume_attempt("auth:global", int(time.time()), 60, 30):
            raise TooManyAttempts
        configured = self.password_hash()
        try:
            PASSWORD_HASHER.verify(configured, password)
        except (VerificationError, InvalidHashError):
            raise InvalidCredentials from None
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        self.repo.create_session(
            hash_token(token), hash_token(configured), now + SESSION_SECONDS, now,
            hash_token(previous_token) if previous_token else None,
        )
        return token

    def require_session(self, token: str | None) -> None:
        configured = self.password_hash()
        if not token or not self.repo.has_session(hash_token(token), hash_token(configured), int(time.time())):
            raise InvalidCredentials

    def logout(self, token: str | None) -> None:
        if token:
            self.repo.delete_session(hash_token(token))
