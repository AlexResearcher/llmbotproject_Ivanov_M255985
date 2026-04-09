from datetime import datetime, timedelta, timezone

import fakeredis.aioredis
import pytest
import pytest_asyncio
from jose import jwt

from app.core.config import settings


class DummyUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class DummyChat:
    def __init__(self, chat_id: int) -> None:
        self.id = chat_id


class DummyMessage:
    def __init__(self, text: str, user_id: int = 111, chat_id: int = 111) -> None:
        self.text = text
        self.from_user = DummyUser(user_id)
        self.chat = DummyChat(chat_id)
        self.answers: list[str] = []

    async def answer(self, text: str) -> None:
        self.answers.append(text)


@pytest.fixture
def make_token():
    def _make_token(sub: str = "123", role: str = "user", expires_minutes: int = 30) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": sub,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)

    return _make_token


@pytest_asyncio.fixture
async def fake_redis(mocker):
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    mocker.patch("app.bot.handlers.get_redis", return_value=redis)
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest.fixture
def message_factory():
    def _factory(text: str, user_id: int = 111, chat_id: int = 111) -> DummyMessage:
        return DummyMessage(text=text, user_id=user_id, chat_id=chat_id)

    return _factory
