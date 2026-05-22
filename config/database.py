import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Annotated
from fastapi import Depends
DEFAULT_URL = "postgresql+asyncpg://related:java7834@127.0.0.1:5433/fastapi_db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_URL)
if os.path.exists("/.dockerenv"):
    DATABASE_URL = DATABASE_URL.replace("127.0.0.1:5433", "db:5432")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

db_dependency = Annotated[AsyncSession, Depends(get_db)]