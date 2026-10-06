import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class DbSession:

    def __init__(self):
        self._database_url = None
        self._engine = None
    
    @property
    def engine(self):
        if self._engine is None:
            self._engine = self.__get_engine()
        return self._engine
    
    @property
    def database_url(self) -> str:
        if self._database_url is None:
            self._database_url = os.environ.get("MISP_DB_URL")
        if not self._database_url:
            raise RuntimeError("MISP_DB_URL environment variable is not set")
        return self._database_url


    def __get_engine(self):
        return create_engine(self.database_url)

    def session(self):
        return sessionmaker(bind=self.engine)()

    def smoke_test_connection(self) -> None:
        with self.engine.connect() as conn:
            db_name = conn.execute(text("select current_database()")).scalar_one()
            version = conn.execute(text("select version()")).scalar_one()

        print("Connected to:", db_name)
        print(version)
