"""
Telegram account linking API.

Endpoints:
  GET  /telegram/connect-code  – Generate unique code for account linking
  GET  /telegram/status        – Check if current user has linked Telegram
  DELETE /telegram/disconnect  – Unlink Telegram account
"""

import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/connect-code",
    summary="Generate a unique Telegram connection code",
    tags=["telegram"],
)
async def generate_connect_code(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Generate a short-lived Telegram connection code.

    User copies this code and sends `/connect <code>` to the bot.
    The bot will then link the Telegram chat to this SmartTender account.
    """
    code = secrets.token_urlsafe(8)
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.telegram_connect_code = code
    db.commit()

    from app.config import get_settings
    bot_username = "SmartTenderKZBot"  # Replace with actual bot username
    return {
        "code": code,
        "instructions": f"Telegram ботына өтіп, мына командані жіберіңіз:",
        "command": f"/connect {code}",
        "bot_link": f"https://t.me/{bot_username}?start=connect_{code}",
    }


@router.get(
    "/status",
    summary="Check Telegram linking status",
    tags=["telegram"],
)
async def telegram_status(
    current_user: User = Depends(get_current_active_user),
):
    """Check whether the current user has a linked Telegram account."""
    return {
        "linked": current_user.telegram_chat_id is not None,
        "telegram_chat_id": current_user.telegram_chat_id,
    }


@router.delete(
    "/disconnect",
    summary="Unlink Telegram account",
    tags=["telegram"],
)
async def telegram_disconnect(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove the Telegram account link."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.telegram_chat_id = None
    user.telegram_connect_code = None
    db.commit()
    return {"message": "Telegram аккаунты ажыратылды."}
