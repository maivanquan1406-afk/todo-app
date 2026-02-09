from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from app.services.user_service import service as user_service
from app.models import UserCreate, UserLogin, UserResponse, Token
from app.core.jwt import decode_token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(payload: UserCreate):
    if not (5 <= len(payload.password) <= 100):
        raise HTTPException(status_code=422, detail="password length must be 5-100")
    if "@" not in payload.email:
        raise HTTPException(status_code=422, detail="invalid email format")
    user = user_service.register(payload)
    if not user:
        raise HTTPException(status_code=409, detail="email already exists")
    return user

@router.post("/login", response_model=Token)
def login(payload: UserLogin):
    token = user_service.login(payload)
    if not token:
        raise HTTPException(status_code=401, detail="invalid email or password")
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid token")
    token = authorization[7:]  # Remove "Bearer " prefix
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="invalid token")
    user = user_service.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid token")
    token = authorization[7:]
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="invalid token")
    user = user_service.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

