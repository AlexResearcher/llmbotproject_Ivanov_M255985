from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.jwt import TokenValidationError, decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request

router = Router()


def build_token_key(tg_user_id: int) -> str:
    return f"token:{tg_user_id}"


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Сначала получите JWT в Auth Service, затем отправьте /token <jwt>."
    )


@router.message(Command("token"))
async def token_command_handler(message: Message) -> None:
    await handle_token_command(message)


@router.message(F.text)
async def text_message_handler(message: Message) -> None:
    if (message.text or "").startswith("/"):
        await message.answer("Неизвестная команда. Используйте /token <jwt>.")
        return
    await handle_text_message(message)


async def handle_token_command(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Отправьте токен в формате /token <jwt>.")
        return

    token = parts[1].strip()
    try:
        decode_and_validate(token)
    except TokenValidationError:
        await message.answer(
            "Токен недействителен или истек. Получите новый JWT в Auth Service."
        )
        return

    redis = get_redis()
    await redis.set(build_token_key(message.from_user.id), token)
    await message.answer("Токен сохранен. Теперь отправьте обычный текстовый запрос.")


async def handle_text_message(message: Message) -> None:
    redis = get_redis()
    token_key = build_token_key(message.from_user.id)
    token = await redis.get(token_key)

    if not token:
        await message.answer(
            "Токен не найден. Сначала авторизуйтесь в Auth Service и отправьте /token <jwt>."
        )
        return

    try:
        decode_and_validate(token)
    except TokenValidationError:
        await redis.delete(token_key)
        await message.answer(
            "Сохраненный токен недействителен или истек. Получите новый JWT и отправьте /token <jwt>."
        )
        return

    llm_request.delay(message.chat.id, message.text or "")
    await message.answer("Запрос принят. Ответ придет следующим сообщением.")
