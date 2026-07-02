import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.cache import TTL_USER_SESSION, cache_key_session, cache_set
from app.core.redis_client import redis_client
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterResponse,
    ResetPasswordRequest,
    Token,
    TokenRefresh,
    UserCreate,
    UserResponse,
    VerifyEmailRequest,
)
from app.tasks.email_tasks import send_password_reset_email, send_verification_email

settings = get_settings()
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter()

PUBLIC_ROLES = {UserRole.BUYER, UserRole.SUPPLIER}


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if user_data.role not in PUBLIC_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Public registration allows only buyer or supplier roles",
        )

    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        is_verified=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = secrets.token_urlsafe(32)
    redis_client.setex(f"verify:{token}", 86400, str(new_user.id))
    verify_link = f"{settings.APP_PUBLIC_URL}/verify-email?token={token}"
    send_verification_email.delay(new_user.email, verify_link)

    return RegisterResponse(
        message="Registration successful. Check your email to verify your account.",
        user=new_user,
    )


@router.post("/verify-email", response_model=UserResponse)
async def verify_email(body: VerifyEmailRequest, db: Session = Depends(get_db)):
    user_id = redis_client.get(f"verify:{body.token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()
    db.refresh(user)
    redis_client.delete(f"verify:{body.token}")
    return user


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Check your inbox for the verification link.",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    cache_set(
        cache_key_session(user.id),
        {"user_id": user.id, "email": user.email, "role": user.role.value},
        TTL_USER_SESSION,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: TokenRefresh, db: Session = Depends(get_db)):
    payload = decode_token(refresh_data.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        return {"message": "If email exists, reset link was sent"}

    token = secrets.token_urlsafe(32)
    redis_client.setex(f"reset:{token}", 3600, str(user.id))
    reset_link = f"{settings.APP_PUBLIC_URL}/reset-password?token={token}"
    send_password_reset_email.delay(user.email, reset_link)
    return {"message": "If email exists, reset link was sent"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    user_id = redis_client.get(f"reset:{body.token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(body.new_password)
    db.commit()
    redis_client.delete(f"reset:{body.token}")
    return {"message": "Password updated successfully"}
