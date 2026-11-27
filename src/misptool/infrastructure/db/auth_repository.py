from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.misptool.infrastructure.db.models import AuthSession, AuthThrottle


class AuthRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_session(self, token_hash: str, password_version: str, expires_at: int, now: int,
                       previous_token_hash: str | None) -> None:
        self.session.execute(delete(AuthSession).where(
            (AuthSession.expires_at <= now) | (AuthSession.password_version != password_version),
        ))
        if previous_token_hash:
            self.session.execute(delete(AuthSession).where(AuthSession.token_hash == previous_token_hash))
        self.session.add(AuthSession(token_hash=token_hash, password_version=password_version, expires_at=expires_at))
        self.session.commit()

    def has_session(self, token_hash: str, password_version: str, now: int) -> bool:
        return self.session.scalar(
            select(AuthSession.token_hash).where(
                AuthSession.token_hash == token_hash, AuthSession.expires_at > now,
                AuthSession.password_version == password_version,
            )
        ) is not None

    def delete_session(self, token_hash: str) -> None:
        self.session.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash))
        self.session.commit()

    def consume_attempt(self, key: str, now: int, window: int, limit: int) -> bool:
        self.session.execute(delete(AuthThrottle).where(AuthThrottle.expires_at <= now))
        statement = insert(AuthThrottle).values(key=key, attempts=1, expires_at=now + window)
        statement = statement.on_conflict_do_update(
            index_elements=[AuthThrottle.key],
            set_={"attempts": case(
                (AuthThrottle.attempts < limit + 1, AuthThrottle.attempts + 1),
                else_=limit + 1,
            )},
        ).returning(AuthThrottle.attempts)
        attempts = self.session.scalar(statement)
        # Commit rejected attempts too, so retries and other workers see the same limit.
        self.session.commit()
        return attempts <= limit
