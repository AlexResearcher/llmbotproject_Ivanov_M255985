import respx
from httpx import Response

from app.core.config import settings
from app.services.openrouter_client import call_openrouter


@respx.mock
async def test_call_openrouter_returns_text_response() -> None:
    route = respx.post(
        f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
    ).mock(
        return_value=Response(
            200,
            json={"choices": [{"message": {"content": "Тестовый ответ от модели"}}]},
        )
    )

    answer = await call_openrouter("Привет")

    assert answer == "Тестовый ответ от модели"
    assert route.called is True
