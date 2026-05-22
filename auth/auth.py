from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from config.database import db_dependency
from config.models import CustomUser
from auth.schemas import CreateUserSchema, LoginRequest, RefreshTokenRequest
from auth.utils import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user, verify_refresh_token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(db: db_dependency, user_data: CreateUserSchema):
    existing_user = await db.execute(
        select(CustomUser).where(
            (CustomUser.username == user_data.username) | 
            (CustomUser.email == user_data.email)
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username yoki email allaqachon mavjud"
        )
    new_user = CustomUser(
        username=user_data.username,
        email=user_data.email,
        phone_number=user_data.phone_number,
        password=hash_password(user_data.password),
        role="Candidate"
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "message": "User created successfully",
        "user_id": str(new_user.id),
        "username": new_user.username
    }

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(db: db_dependency, login_data: LoginRequest):
    """Login qilish va tokenlar olish"""
    
    query = select(CustomUser).where(CustomUser.username == login_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username yoki parol xato"
        )
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 15 * 60,
        "user_id": str(user.id),
        "username": user.username,
        "role": user.role
    }

@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_access_token(db: db_dependency, refresh_request: RefreshTokenRequest):
    """Refresh token yordamida yangi access token olish"""
    
    user = await verify_refresh_token(refresh_request.refresh_token, db)
    
    token_data = {"sub": str(user.id)}
    new_access_token = create_access_token(data=token_data)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": 15 * 60
    }

@router.get("/profile", status_code=status.HTTP_200_OK)
async def get_profile(current_user: CustomUser = Depends(get_current_user)):
    """Foydalanuvchi profilini olish"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_staff": current_user.is_staff
    }