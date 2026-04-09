import httpx

from app.core.config import settings


async def call_openrouter(prompt: str) -> str:
    url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_site_url,
        "X-Title": settings.openrouter_app_name,
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise RuntimeError("Failed to reach OpenRouter.") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter request failed with status {response.status_code}: {response.text[:200]}"
        )

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("OpenRouter response has unexpected format.") from exc

    if not content:
        raise RuntimeError("OpenRouter returned an empty response.")

    return content
