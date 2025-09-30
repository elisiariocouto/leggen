"""Database connection and session management using SQLModel."""

from contextlib import contextmanager
from typing import Generator

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

from leggen.utils.paths import path_manager

_engine = None


def get_database_url() -> str:
    """Get the database URL for SQLAlchemy."""
    db_path = path_manager.get_database_path()
    return f"sqlite:///{db_path}"


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        db_url = get_database_url()
        _engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    return _engine


def create_db_and_tables():
    """Create all database tables."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created/verified")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session context manager.

    Usage:
        with get_session() as session:
            result = session.exec(select(Account)).all()
    """
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def init_database():
    """Initialize the database with tables."""
    create_db_and_tables()
