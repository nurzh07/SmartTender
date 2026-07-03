from pydantic import BaseModel, EmailStr, field_validator
from datetime import date, datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: UserRole = UserRole.SUPPLIER


class UserCreate(UserBase):
    password: str
    bin: str | None = None  # Kazakhstan BIN (12 digits)
    company_official_name: str | None = None  # Company name (optional)

    @field_validator("bin")
    @classmethod
    def validate_bin(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if v == "":
            return None
        if len(v) != 12 or not v.isdigit():
            raise ValueError("БИН 12 цифрдан тұруы керек")
        return v


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool = False
    department_id: int | None = None
    created_at: datetime

    # BIN verification fields
    bin: str | None = None
    bin_verified: bool = False
    company_official_name: str | None = None
    company_registration_date: date | None = None
    company_status: str | None = None
    bin_verified_at: datetime | None = None

    class Config:
        from_attributes = True


class RegisterResponse(BaseModel):
    message: str
    user: UserResponse


class VerifyEmailRequest(BaseModel):
    token: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
