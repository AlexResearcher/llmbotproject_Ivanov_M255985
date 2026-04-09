from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.users import UsersRepository
from app.schemas.auth import TokenResponse


class AuthUseCase:
    def __init__(self, users_repo: UsersRepository) -> None:
        self.users_repo = users_repo

    async def register(self, *, email: str, password: str) -> User:
        existing_user = await self.users_repo.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError()

        try:
            return await self.users_repo.create(
                email=email,
                password_hash=hash_password(password),
            )
        except IntegrityError as exc:
            await self.users_repo.session.rollback()
            raise UserAlreadyExistsError() from exc

    async def login(self, *, email: str, password: str) -> TokenResponse:
        user = await self.users_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        token = create_access_token(sub=user.id, role=user.role)
        return TokenResponse(access_token=token)

    async def me(self, *, user_id: int) -> User:
        user = await self.users_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return user
