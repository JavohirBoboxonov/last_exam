from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Annotated
from fastapi import Depends

DATABASE_URL = "postgresql+asyncpg://related:java7834@fastapi_db/fastapi_db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine)
Base = declarative_base()
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

db_dependency = Annotated[AsyncSession, Depends(get_db)]