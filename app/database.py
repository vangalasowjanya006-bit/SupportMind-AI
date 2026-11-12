from os import getenv

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

_engine = None
_session_factory = None


def get_engine():
    global _engine

    if _engine is None:
        database_url = getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not configured")
        _engine = create_engine(database_url, echo=False, pool_pre_ping=True)

    return _engine


def SessionLocal():
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
        )

    return _session_factory()


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()