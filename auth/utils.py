from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from config.database import db_dependency
from config.models import CustomUser
import hashlib
import base64
import bcrypt
import uuid

# ========== KONFIGURATSIYA ==========
SECRET_KEY = "your-super-secret-key-change-this-in-production-2024"
REFRESH_SECRET_KEY = "your-refresh-secret-key-different-from-access-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ========== PAROL FUNKSIYALARI (PASSLIBSIZ) ==========
def hash_password(password: str) -> str:
    """
    Parolni SHA256 + Bcrypt bilan hash qilish
    Hech qanday 72 bayt cheklovi YO'Q!
    """
    # 1. SHA256 hash (32 bayt)
    sha256_hash = hashlib.sha256(password.encode('utf-8')).digest()
    
    # 2. Base64 encode (44 bayt)
    safe_string = base64.b64encode(sha256_hash).decode('ascii')
    
    # 3. Bcrypt hash (to'g'ridan-to'g'ri, passlibsiz)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(safe_string.encode('utf-8'), salt)
    
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Parolni tekshirish
    """
    try:
        # 1. Kiritilgan parolni SHA256 qilish
        sha256_hash = hashlib.sha256(plain_password.encode('utf-8')).digest()
        
        # 2. Base64 encode
        safe_string = base64.b64encode(sha256_hash).decode('ascii')
        
        # 3. Bcrypt bilan solishtirish
        return bcrypt.checkpw(safe_string.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

# ========== TOKEN FUNKSIYALARI ==========
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Access token yaratadi"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    """Refresh token yaratadi"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_refresh_token(refresh_token: str, db: db_dependency):
    """Refresh tokenni tekshirish"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token noto'g'ri yoki muddati o'tgan",
    )
    
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    query = select(CustomUser).where(CustomUser.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: db_dependency = None):
    """Access tokenni tekshirib, foydalanuvchini qaytaradi"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token noto'g'ri yoki muddati o'tgan",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    query = select(CustomUser).where(CustomUser.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user