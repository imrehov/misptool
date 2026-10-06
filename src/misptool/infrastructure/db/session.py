import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    database_url = os.environ.get("MISP_DB_URL")
    if not database_url:
        raise RuntimeError("MISP_DB_URL environment variable is not set")
    return database_url


def get_engine():
    return create_engine(get_database_url())


SessionLocal = sessionmaker(bind=get_engine())


def smoke_test_connection() -> None:
    with get_engine().connect() as conn:
        db_name = conn.execute(text("select current_database()")).scalar_one()
        version = conn.execute(text("select version()")).scalar_one()

    print("Connected to:", db_name)
    print(version)
