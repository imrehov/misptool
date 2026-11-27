import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.misptool.api.app import app
from src.misptool.api.dependencies import get_auth_repo, get_config, get_event_state_repo
from src.misptool.application.auth_service import PASSWORD_HASHER, hash_token
from src.misptool.infrastructure.db.auth_repository import AuthRepository
from src.misptool.infrastructure.db.models import AuthSession, AuthThrottle, Base


PASSWORD = "a long test passphrase"
PASSWORD_HASH = PASSWORD_HASHER.hash(PASSWORD)
HEADERS = {"X-CSRF-Protection": "1", "Origin": "http://localhost:5173"}


class EmptyEvents:
    def list_event_states(self, filters):
        return []

    def get_event_state(self, event_id):
        return None

    def list_event_changes(self, event_id):
        return []


@pytest.fixture
def auth_client(monkeypatch):
    monkeypatch.setenv("APP_PASSWORD_HASH", PASSWORD_HASH)
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setenv("AUTH_ALLOWED_ORIGINS", "http://localhost:5173")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def repository():
        with Session(engine) as session:
            yield AuthRepository(session)

    app.dependency_overrides[get_auth_repo] = repository
    app.dependency_overrides[get_event_state_repo] = lambda: EmptyEvents()
    app.dependency_overrides[get_config] = lambda: {"misp": {"url": "https://misp.example"}}
    with TestClient(app, base_url="https://localhost") as client:
        yield client, engine
    app.dependency_overrides.clear()
    engine.dispose()


def login(client, password=PASSWORD):
    return client.post("/auth/login", headers=HEADERS, json={"password": password})


@pytest.mark.parametrize("path", ["/events", "/events/123", "/events/123/changes", "/auth/session"])
def test_every_private_endpoint_requires_session(auth_client, path):
    client, _ = auth_client
    assert client.get(path).status_code == 401
    client.cookies.set("misptool_session", "forged-token")
    assert client.get(path).status_code == 401
    assert client.get("/health").json() == {"status": "ok"}


def test_login_session_rotation_expiry_and_logout(auth_client):
    client, engine = auth_client
    response = login(client)
    assert response.status_code == 204
    assert response.content == b""
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "secure" in cookie and "samesite=lax" in cookie
    assert "max-age=28800" in cookie
    token = client.cookies.get("misptool_session")
    with Session(engine) as session:
        stored = session.get(AuthSession, hash_token(token))
        assert stored is not None and stored.token_hash != token
        assert stored.password_version == hash_token(PASSWORD_HASH)
    assert client.get("/auth/session").status_code == 204
    assert client.get("/events").json() == []
    assert client.get("/events/missing").status_code == 404
    assert client.get("/events/123/changes").json() == []
    assert client.get("/events").headers["cache-control"] == "no-store"

    login(client)
    assert token != client.cookies.get("misptool_session")
    with Session(engine) as session:
        assert session.get(AuthSession, hash_token(token)) is None
        session.execute(update(AuthSession).values(expires_at=int(time.time()) - 1))
        session.commit()
    assert client.get("/auth/session").status_code == 401
    login(client)
    last_token = client.cookies.get("misptool_session")
    assert client.post("/auth/logout", headers=HEADERS).status_code == 204
    assert client.cookies.get("misptool_session") is None
    client.cookies.set("misptool_session", last_token)
    assert client.get("/events").status_code == 401


def test_password_rotation_invalidates_all_sessions(auth_client, monkeypatch):
    client, engine = auth_client
    assert login(client).status_code == 204
    first_token = client.cookies.get("misptool_session")
    client.cookies.clear()
    assert login(client).status_code == 204
    second_token = client.cookies.get("misptool_session")
    new_password = "a different long password"
    monkeypatch.setenv("APP_PASSWORD_HASH", PASSWORD_HASHER.hash(new_password))
    for token in (first_token, second_token):
        client.cookies.clear()
        client.cookies.set("misptool_session", token)
        assert client.get("/events").status_code == 401
    assert login(client).status_code == 401
    assert login(client, new_password).status_code == 204
    assert client.get("/events").status_code == 200
    with Session(engine) as session:
        assert session.get(AuthSession, hash_token(first_token)) is None
        assert session.get(AuthSession, hash_token(second_token)) is None


@pytest.mark.parametrize("configured", [None, "", "not-a-hash", "$argon2id$broken"])
def test_missing_or_invalid_hash_fails_closed(auth_client, monkeypatch, configured):
    client, _ = auth_client
    login(client)
    if configured is None:
        monkeypatch.delenv("APP_PASSWORD_HASH")
    else:
        monkeypatch.setenv("APP_PASSWORD_HASH", configured)
    assert login(client).status_code == 401
    assert client.get("/events").status_code == 401


def test_invalid_password_creates_no_session(auth_client):
    client, engine = auth_client
    response = login(client, "incorrect")
    assert response.status_code == 401
    assert PASSWORD not in response.text
    with Session(engine) as session:
        assert session.scalar(select(AuthSession)) is None


@pytest.mark.parametrize("data", [
    {"password": ""}, {"password": "x" * 129}, {},
    {"password": PASSWORD, "username": "alice"},
])
def test_login_validates_input_without_echoing_password(auth_client, data):
    client, _ = auth_client
    response = client.post("/auth/login", headers=HEADERS, json=data)
    assert response.status_code == 422
    assert PASSWORD not in response.text
    assert all("input" not in error for error in response.json()["detail"])


def test_account_endpoints_are_removed(auth_client):
    client, _ = auth_client
    assert client.post("/auth/register", headers=HEADERS, json={}).status_code == 404
    assert client.get("/auth/me").status_code == 404
    assert "users" not in Base.metadata.tables


@pytest.mark.parametrize("path", ["/auth/login", "/auth/logout"])
def test_csrf_protection_covers_every_auth_post(auth_client, path):
    client, _ = auth_client
    assert client.post(path, json={}).status_code == 403
    assert client.post(path, headers={**HEADERS, "Origin": "https://evil.example"}, json={}).status_code == 403
    preflight = client.options(path, headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "X-CSRF-Protection",
    })
    assert "access-control-allow-origin" not in preflight.headers


def test_vite_origin_can_send_credentials_and_csrf_header(auth_client):
    client, _ = auth_client
    response = client.options("/auth/login", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,X-CSRF-Protection",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_login_throttling_persists_and_expires(auth_client):
    client, engine = auth_client
    for _ in range(30):
        assert login(client, "incorrect").status_code == 401
    assert login(client).status_code == 429
    with Session(engine) as session:
        session.execute(update(AuthThrottle).values(expires_at=0))
        session.commit()
    assert login(client).status_code == 204


def test_local_http_cookie_mode(auth_client, monkeypatch):
    client, _ = auth_client
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    assert "secure" not in login(client).headers["set-cookie"].lower()


def test_shared_password_migration_preserves_events_and_removes_accounts(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import MetaData, Table, inspect

    url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("MISP_DB_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "c7b2e91a6d04")
    engine = create_engine(url)
    try:
        metadata = MetaData()
        users = Table("users", metadata, autoload_with=engine)
        old_sessions = Table("auth_sessions", metadata, autoload_with=engine)
        events = Table("event_states", metadata, autoload_with=engine)
        changes = Table("event_changes", metadata, autoload_with=engine)
        with engine.begin() as conn:
            conn.execute(users.insert().values(id=1, username="alice", password_hash=PASSWORD_HASH))
            conn.execute(old_sessions.insert().values(token_hash="old-session", user_id=1, expires_at=9999999999))
            conn.execute(events.insert().values(
                event_id="42", info="keep this event", date="2026-11-27", timestamp="1",
                publish_timestamp="1", published=True, threat_level_id="1", analysis="0",
                attribute_count=0, object_count=0, score=1, fingerprint="keep",
                tag_names=[], galaxy_tag_names=[],
            ))
            conn.execute(changes.insert().values(
                event_id="42", change_type="new", new_fingerprint="keep", new_score=1,
                change_summary=["new event"], observed_at="2026-11-27",
            ))
        command.upgrade(config, "head")
        inspector = inspect(engine)
        assert "users" not in inspector.get_table_names()
        assert {column["name"] for column in inspector.get_columns("auth_sessions")} == {
            "token_hash", "password_version", "expires_at",
        }
        with Session(engine) as session:
            assert session.scalar(select(AuthSession)) is None
            assert session.scalar(select(events.c.info)) == "keep this event"
            assert session.scalar(select(changes.c.change_summary)) == ["new event"]
        command.downgrade(config, "c7b2e91a6d04")
        assert "users" in inspect(engine).get_table_names()
        command.upgrade(config, "head")
    finally:
        engine.dispose()


def test_password_generator_outputs_quoted_argon2id_hash(monkeypatch, capsys):
    from scripts import hash_password

    monkeypatch.setattr(hash_password, "getpass", lambda prompt: PASSWORD)
    hash_password.main()
    output = capsys.readouterr().out.strip()
    assert output.startswith("APP_PASSWORD_HASH='$argon2id$") and output.endswith("'")
    assert PASSWORD not in output
    assert PASSWORD_HASHER.verify(output.split("'", 2)[1], PASSWORD)


@pytest.mark.parametrize("answers", [["short"], [PASSWORD, "does not match"]])
def test_password_generator_rejects_invalid_input(monkeypatch, capsys, answers):
    from scripts import hash_password

    values = iter(answers)
    monkeypatch.setattr(hash_password, "getpass", lambda prompt: next(values))
    with pytest.raises(SystemExit):
        hash_password.main()
    assert capsys.readouterr().out == ""
