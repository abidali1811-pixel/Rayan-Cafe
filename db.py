from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from models import Base

_engine = None
SessionLocal = scoped_session(sessionmaker(autoflush=False, autocommit=False))


def init_engine(database_url: str, echo: bool = False):
    global _engine
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    _engine = create_engine(database_url, echo=echo, future=True, connect_args=connect_args)
    SessionLocal.configure(bind=_engine)
    return _engine


def get_engine():
    if _engine is None:
        raise RuntimeError("Database engine is not initialized")
    return _engine


def create_tables():
    Base.metadata.create_all(bind=get_engine())


def drop_tables():
    Base.metadata.drop_all(bind=get_engine())
