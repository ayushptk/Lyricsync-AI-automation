from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import User
from auth.schemas import UserCreate, UserLogin, UserResponse
from auth.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE_SECURE = False # Set to True in production (HTTPS)

@router.post("/register", response_model=UserResponse)
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, password_hash=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # In a real app, you would send a verification email here.
    return new_user

@router.post("/login")
def login(request: Request, response: Response, user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = create_access_token(subject=str(user.id), role=user.role)
    refresh_token = create_refresh_token(subject=str(user.id))
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=15 * 60 # 15 minutes
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=7 * 24 * 60 * 60 # 7 days
    )
    
    return {"message": "Login successful"}

@router.post("/refresh")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
        
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")
        
    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    new_access_token = create_access_token(subject=str(user.id), role=user.role)
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=15 * 60
    )
    
    return {"message": "Token refreshed"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
