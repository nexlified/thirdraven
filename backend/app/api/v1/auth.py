from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.crud.user import (
    create_password_reset_token,
    create_user,
    get_user_by_username,
    get_user_preferences,
    reset_password_with_token,
    update_user_preferences,
)
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserPreferencesPublic,
    UserPreferencesUpdate,
    UserPublic,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    existing = await get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    return await create_user(db, user_in)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    user = await get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.username})
    return Token(access_token=token)


@router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.get("/me/preferences", response_model=UserPreferencesPublic)
async def get_preferences(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return UserPreferencesPublic(**get_user_preferences(current_user))


@router.patch("/me/preferences", response_model=UserPreferencesPublic)
async def patch_preferences(
    data: UserPreferencesUpdate,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    prefs = await update_user_preferences(
        db,
        current_user,
        data.model_dump(exclude_unset=True),
    )
    return UserPreferencesPublic(**prefs)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    token = await create_password_reset_token(db, data.email)
    return ForgotPasswordResponse(
        message="If the account exists, a reset token has been generated.",
        reset_token=token,
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters"
        )
    ok = await reset_password_with_token(db, data.reset_token, data.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return MessageResponse(message="Password updated successfully")

