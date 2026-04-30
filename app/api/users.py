from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.deps import get_db
from app.db.models.users import User
from app.db.schemas.users import UserCreate, UserRead, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.crud import users as crud_users
from app.core.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await crud_users.get_user_by_username(db, username=user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists. Choose a different username.",
        )
    existing_email = await crud_users.get_user_by_email(db, email=user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists. Choose a different email address.",
        )
    user = await crud_users.create_user(db, user_in=user_in)
    return user


@router.get("/", response_model=List[UserRead])
async def list_users(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.get("/profile", response_model=UserRead)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the profile of the currently authenticated user."""
    return current_user


@router.put("/profile", response_model=UserRead)
async def update_profile(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the profile of the currently authenticated user."""
    update_data = user_in.model_dump(exclude_unset=True)

    sensitive_fields = {"username", "email", "new_password"}
    if sensitive_fields.intersection(update_data.keys()):
        if not user_in.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Current password is required to change your username, email, or password."
                ),
            )
        if not verify_password(user_in.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

    if user_in.username is not None and user_in.username != current_user.username:
        existing = await crud_users.get_user_by_username(db, username=user_in.username)
        if existing and str(existing.id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists. Choose a different username.",
            )
        current_user.username = user_in.username

    if user_in.email is not None and user_in.email != current_user.email:
        existing = await crud_users.get_user_by_email(db, email=user_in.email)
        if existing and str(existing.id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists. Choose a different email address.",
            )
        current_user.email = user_in.email

    if user_in.new_password is not None:
        if not user_in.new_password.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The new password cannot be empty.",
            )
        if user_in.new_password != user_in.confirm_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The password confirmation does not match the new password.",
            )
        current_user.hashed_password = get_password_hash(user_in.new_password)

    if user_in.first_name is not None:
        current_user.first_name = user_in.first_name
    if user_in.last_name is not None:
        current_user.last_name = user_in.last_name
    if user_in.phone_number is not None:
        current_user.phone_number = user_in.phone_number

    current_user.updated_at = datetime.utcnow()  # type: ignore[attr-defined]

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID, user_in: UserUpdate, db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_in.username is not None:
        user.username = user_in.username
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.new_password is not None:
        user.hashed_password = get_password_hash(user_in.new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return None
