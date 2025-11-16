"""Async database configuration with singleton pattern."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import logger

# Base class for ORM models
Base = declarative_base()


class DatabaseManager:
    """Async-safe singleton database manager."""

    _instance: Optional["DatabaseManager"] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database manager only once."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._setup_engine()

    def _setup_engine(self):
        """Setup async database engine."""
        try:
            self._engine = create_async_engine(
                settings.database_url_async,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                echo=settings.DB_ECHO,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {str(e)}")
            raise

    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker:
        """Get session factory."""
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized")
        return self._session_factory

    async def create_tables(self):
        """Create all database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise

    async def close(self):
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connections closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with context manager."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


def get_db_manager() -> DatabaseManager:
    """Get singleton database manager instance."""
    return DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes to get database session."""
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        yield session


# Global database manager instance
db_manager = get_db_manager()
