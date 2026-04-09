import asyncio

from app.bot.dispatcher import create_bot, create_dispatcher


async def main() -> None:
    bot = create_bot()
    dispatcher = create_dispatcher()
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
