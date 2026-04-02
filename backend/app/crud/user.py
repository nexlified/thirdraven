import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import hash_password, verify_password
from app.models.person import Person
from app.models.user import User
from app.schemas.user import UserCreate


def _default_preferences() -> dict[str, Any]:
    return {
        "default_country": "",
        "default_timezone": "",
        "default_relationship_nature": "",
        "default_visibility": "private",
        "default_closeness_level": None,
        "default_languages": [],
    }


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def get_user_preferences(user: User) -> dict[str, Any]:
    current = user.preferences if isinstance(user.preferences, dict) else {}
    merged = {**_default_preferences(), **current}
    if not isinstance(merged.get("default_languages"), list):
        merged["default_languages"] = []
    if merged.get("default_visibility") not in {"private", "household"}:
        merged["default_visibility"] = "private"
    if merged.get("default_relationship_nature") not in {
        "",
        "personal",
        "professional",
        "mixed",
    }:
        merged["default_relationship_nature"] = ""
    return merged


async def update_user_preferences(
    db: AsyncSession,
    user: User,
    updates: dict[str, Any],
) -> dict[str, Any]:
    base = get_user_preferences(user)
    cleaned = {k: v for k, v in updates.items() if v is not None}
    base.update(cleaned)
    user.preferences = base
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return get_user_preferences(user)


async def create_password_reset_token(db: AsyncSession, email: str) -> str | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None

    raw_token = secrets.token_urlsafe(32)
    user.reset_password_token_hash = hash_password(raw_token)
    user.reset_password_token_expires_at = datetime.now(UTC) + timedelta(hours=1)
    db.add(user)
    await db.commit()
    return raw_token


async def reset_password_with_token(
    db: AsyncSession,
    reset_token: str,
    new_password: str,
) -> bool:
    now = datetime.now(UTC)
    result = await db.execute(
        select(User).where(
            User.reset_password_token_hash.is_not(None),
            User.reset_password_token_expires_at.is_not(None),
            User.reset_password_token_expires_at > now,
        )
    )
    users = result.scalars().all()

    for user in users:
        token_hash = user.reset_password_token_hash or ""
        if verify_password(reset_token, token_hash):
            user.hashed_password = hash_password(new_password)
            user.reset_password_token_hash = None
            user.reset_password_token_expires_at = None
            db.add(user)
            await db.commit()
            return True
    return False


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Create a user and atomically create their self-person record.

    Steps:
    1. Insert user (person_id = NULL)
    2. Insert person (is_self = True, owner_id = user.id)
    3. Update user.person_id = person.id
    4. Commit once
    """
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        person_id=None,
        preferences=_default_preferences(),
    )
    db.add(user)
    await db.flush()  # assigns user.id without committing

    self_person = Person(
        id=uuid.uuid7(),
        owner_id=user.id,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        is_self=True,
    )
    db.add(self_person)
    await db.flush()  # assigns self_person.id

    user.person_id = self_person.id
    await db.commit()
    await db.refresh(user)
    return user
