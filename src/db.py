"""
src/db.py — Postgres connection shared by everything that stores data.

Schema changes go through Alembic migrations (migrations/), never create_all().
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config import settings

# pool_pre_ping drops dead connections (e.g. after a DB restart) instead of erroring
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
