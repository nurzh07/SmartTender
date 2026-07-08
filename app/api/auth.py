import logging
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
from app.tasks.email_tasks import send_password_reset_email, send_verification_email, send_welcome_email
from app.services.email_utils import send_welcome_email as send_welcome_email_resend, send_password_reset_email as send_password_reset_email_resend, send_verification_email as send_verification_email_resend

settings = get_settings()
logger = logging.getLogger(__name__)
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
    print(f"[DEBUG] Register request: email={user_data.email}, role={user_data.role}, role_type={type(user_data.role)}")
    print(f"[DEBUG] PUBLIC_ROLES: {PUBLIC_ROLES}")
    print(f"[DEBUG] Role check: {user_data.role} in PUBLIC_ROLES = {user_data.role in PUBLIC_ROLES}")

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
        bin=user_data.bin,
        bin_verified=False,
        company_official_name=user_data.company_official_name,
    )

    # ── BIN Verification ──────────────────────────────────────
    if user_data.bin:
        try:
            from app.services.bin_verification import verify_bin
            from datetime import datetime as dt

            bin_result = await verify_bin(user_data.bin)
            if bin_result["valid"]:
                new_user.bin_verified = True
                new_user.company_official_name = bin_result["company_name"]
                # Parse registration date if available
                if bin_result["registration_date"]:
                    try:
                        new_user.company_registration_date = dt.strptime(
                            bin_result["registration_date"], "%Y-%m-%d"
                        ).date()
                    except:
                        pass
                new_user.company_status = bin_result["company_status"]
                new_user.bin_verified_at = dt.utcnow()
            else:
                # BIN not found in government registry
                if bin_result["error"] and ("табылмады" in bin_result["error"] or "not found" in bin_result["error"].lower()):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="БИН табылмады — мемлекеттік тізілімде мұндай БИН жоқ",
                    )
                # API timeout / down → allow registration, mark as unverified
                new_user.bin_verified = False
        except HTTPException:
            raise
        except Exception as e:
            # API error - allow registration but mark as unverified
            logger.error(f"BIN verification failed: {e}")
            new_user.bin_verified = False
    # ──────────────────────────────────────────────────────────

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = secrets.token_urlsafe(32)
    redis_client.setex(f"verify:{token}", 86400, str(new_user.id))
    verify_link = f"{settings.APP_PUBLIC_URL}/verify-email?token={token}"
    send_verification_email.delay(new_user.email, verify_link)
    
    # Send welcome email and verification email using Resend
    send_verification_email_resend(new_user.email, verify_link)
    send_welcome_email_resend(new_user.email, new_user.full_name or new_user.email)

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

    # Email verification disabled for demo mode
    # if not user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Email not verified. Check your inbox for the verification link.",
    #     )

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
    print(f"[PASSWORD RESET] {user.email} -> {reset_link}")
    send_password_reset_email.delay(user.email, reset_link)
    # Send password reset email using Resend
    send_password_reset_email_resend(user.email, reset_link)
    return {
        "message": "If email exists, reset link was sent. In local development, the link is also printed to the server console.",
        "reset_link": reset_link,
    }


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
