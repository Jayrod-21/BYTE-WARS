"""
database.py — Database connection and session management for BYTE Wars.

Sets up the async SQLAlchemy engine and session factory using the DATABASE_URL
environment variable. Also provides the Base class for all ORM models.
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Pull the database URL from environment, with a local fallback for testing
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://bytewars:bytewars_dev@localhost:5432/bytewars"
)

# Create the async engine — echo=False in production, True for debugging
engine = create_async_engine(DATABASE_URL, echo=False)

# Session factory — each request gets its own session
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models in BYTE Wars."""
    pass


async def get_db():
    """
    Dependency that yields a database session.
    Used with FastAPI's Depends() for request-scoped DB access.
    """
    async with async_session() as session:
        yield session
