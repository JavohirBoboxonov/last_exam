from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import jwt

# O'zingizning importlaringizni tekshiring
from auth import utils 
from config.database import get_db
from config.models import CustomUser

security = HTTPBearer()

# 1. JUDA MUHIM: 'async def' deb yozilganiga ishonch hosil qiling
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> CustomUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        user_id = payload.get("sub") 
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token yaroqsiz")
        stmt = select(CustomUser).where(CustomUser.id == user_id)
        result = await db.execute(stmt)  # 3. 'await' so'zi shart!
        user = result.scalars().first()
        
        if user is None:
            raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi")
        
        return user
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token xatosi")

def require_roles(allowed_roles: List[str]):
    async def role_checker(current_user: CustomUser = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ruxsat yo'q"
            )
        return current_user
    return role_checker