import asyncio

import httpx

from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import call_openrouter


def _send_telegram_message(chat_id: int, text: str) -> None:
    if not settings.telegram_bot_token:
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        response = httpx.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError("Failed to send Telegram message.") from exc


@celery_app.task(name="app.tasks.llm_tasks.llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> str:
    try:
        answer = asyncio.run(call_openrouter(prompt))
    except Exception as exc:  # noqa: BLE001
        answer = f"Ошибка при обращении к LLM: {exc}"

    _send_telegram_message(tg_chat_id, answer)
    return answer
