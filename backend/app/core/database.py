"""
OmniSynth - Database Configuration
Async SQLAlchemy with SQLite (sandbox) / PostgreSQL (production)
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData, text
from app.core.config import settings
from loguru import logger

# Naming convention for constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Detect database type
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # Use NullPool for SQLite: every request gets a brand-new connection.
    # This avoids the "attempt to write a readonly database" error that occurs
    # when aiosqlite reuses a pooled connection across async greenlet boundaries.
    from sqlalchemy.pool import NullPool
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=NullPool,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=300,
    )

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    from app.models import user, research, collaboration  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully")
    await _create_default_admin()


async def _create_default_admin():
    """Create default superuser if none exists."""
    from sqlalchemy import select, func
    from app.models.user import User, UserRole, UserStatus
    from app.core.security import get_password_hash
    import uuid

    async with AsyncSessionLocal() as session:
        try:
            count = (await session.execute(
                select(func.count(User.id)).where(User.is_superuser == True)
            )).scalar() or 0

            if count == 0:
                admin = User(
                    id=uuid.uuid4(),
                    email=settings.FIRST_SUPERUSER_EMAIL,
                    username="admin",
                    full_name="System Admin",
                    hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                    role=UserRole.ADMIN,
                    status=UserStatus.ACTIVE,
                    is_active=True,
                    is_superuser=True,
                    is_verified=True,
                )
                session.add(admin)
                await session.commit()
                logger.info(f"Default admin created: {settings.FIRST_SUPERUSER_EMAIL}")
        except Exception as e:
            logger.warning(f"Admin creation skipped: {e}")
            await session.rollback()


async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
