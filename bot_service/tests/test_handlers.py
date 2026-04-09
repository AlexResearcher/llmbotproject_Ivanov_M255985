from app.bot.handlers import build_token_key, handle_text_message, handle_token_command


async def test_token_command_saves_token(fake_redis, make_token, message_factory) -> None:
    token = make_token(sub="777")

    message = message_factory(f"/token {token}")

    await handle_token_command(message)

    assert await fake_redis.get(build_token_key(111)) == token
    assert "Токен сохранен" in message.answers[-1]


async def test_text_without_saved_token_denies_access(
    fake_redis,
    mocker,
    message_factory,
) -> None:
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")
    message = message_factory("Расскажи про JWT")

    await handle_text_message(message)

    delay_mock.assert_not_called()
    assert "Токен не найден" in message.answers[-1]


async def test_text_with_saved_token_enqueues_task(
    fake_redis,
    mocker,
    make_token,
    message_factory,
) -> None:
    token = make_token(sub="555")
    await fake_redis.set(build_token_key(111), token)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")
    message = message_factory("Объясни, что такое Celery")

    await handle_text_message(message)

    delay_mock.assert_called_once_with(111, "Объясни, что такое Celery")
    assert "Запрос принят" in message.answers[-1]
