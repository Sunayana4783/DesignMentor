"""User registration, login, and token management."""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User
from app.models.progress import UserProgress
from app.models.curriculum import Concept
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.logging import logger


class UserService:

    @staticmethod
    async def register(req: RegisterRequest, db: AsyncSession) -> User:
        # Check uniqueness
        existing = await db.execute(
            select(User).where((User.email == req.email) | (User.username == req.username))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already taken")

        user = User(
            email=req.email,
            username=req.username,
            hashed_password=hash_password(req.password),
            full_name=req.full_name,
        )
        db.add(user)
        await db.flush()

        # Unlock the very first concept (OOP foundation)
        first_concept = await db.execute(
            select(Concept)
            .where(Concept.is_active == True)
            .order_by(Concept.order_index)
            .limit(1)
        )
        first = first_concept.scalar_one_or_none()
        if first:
            progress = UserProgress(
                user_id=user.id,
                concept_id=first.id,
                is_unlocked=True,
            )
            db.add(progress)

        await db.commit()
        await db.refresh(user)
        logger.info("user_registered", user_id=str(user.id), username=user.username)
        return user

    @staticmethod
    async def login(req: LoginRequest, db: AsyncSession) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == req.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        logger.info("user_login", user_id=str(user.id))
        return TokenResponse(access_token=access, refresh_token=refresh)

    @staticmethod
    async def refresh_tokens(refresh_token: str, db: AsyncSession) -> TokenResponse:
        from jose import JWTError
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
            user_id = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )
