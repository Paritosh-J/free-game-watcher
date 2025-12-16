import logging
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.config import settings

logger = logging.getLogger(__name__)

# Database setup
try:
    DATABASE_URL = settings.DATABASE_URL
    logger.info("✅ Database URL successfully retrieved from settings.")
except AttributeError as e:
    logger.error(f"❌ Error accessing DATABASE_URL from settings: {e}")
    raise

# Async engine
try:
    engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, future=True)
    logger.info("✅ Asynchronous database engine created successfully.")
except Exception as e:
    logger.error(f"❌ Failed to create database engine: {e}", exc_info=True)
    raise

async def init_db():
    logger.info("ℹ️ Initializing database: attempting to create all tables if they do not exist.")
    try:
        # create tables (synchronous call to metadata create_all via run_sync)
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("✅ Database initialization complete.")
    except Exception as e:
        logger.error(f"❌ An error occurred during database initialization in init_db: {e}", exc_info=True)
        raise
        
# helper to get async session
def get_session() -> AsyncSession:
    logger.debug("ℹ️ Providing a new asynchronous database session.")
    return AsyncSession(engine)