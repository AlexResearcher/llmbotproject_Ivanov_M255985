from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError
from app.core.security import decode_token
from app.db.models import User
from app.db.session import AsyncSessionLocal
from app.repositories.users import UsersRepository
from app.usecases.auth import AuthUseCase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_users_repo(session: Annotated[AsyncSession, Depends(get_db)]) -> UsersRepository:
    return UsersRepository(session)


def get_auth_uc(
    users_repo: Annotated[UsersRepository, Depends(get_users_repo)],
) -> AuthUseCase:
    return AuthUseCase(users_repo)


async def get_current_user_id(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> int:
    if not token:
        raise InvalidTokenError("Missing bearer token.")

    payload = decode_token(token)
    return int(payload["sub"])


async def get_current_user(
    user_id: Annotated[int, Depends(get_current_user_id)],
    auth_uc: Annotated[AuthUseCase, Depends(get_auth_uc)],
) -> User:
    return await auth_uc.me(user_id=user_id)
