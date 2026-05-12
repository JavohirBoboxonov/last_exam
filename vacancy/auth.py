# auth.py (autentifikatsiya uchun)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import jwt

from config.database import get_db
from config.models import CustomUser

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> CustomUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(CustomUser).filter(CustomUser.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_roles(allowed_roles: List[str]):
    """Faqat allowed_roles dagilar kirishi mumkin"""
    def role_checker(current_user: CustomUser = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role} not allowed. Required: {allowed_roles}"
            )
        return current_user
    return role_checker