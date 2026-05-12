from fastapi import FastAPI, status, Depends, HTTPException
from config.database import Base, engine, AsyncSessionLocal
from typing import Annotated
from auth import auth
from config import models
from vacancy import api
from status import application



app = FastAPI()
app.include_router(auth.router)
app.include_router(api.router)
app.include_router(application.router)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)