import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from utils.config import config
from utils.logging_config import setup_logging
from db.repository import init_db
from handlers.start import router as start_router
from handlers.contracts import router as contract_router
from services.http_server import start_http_server

async def main():
    setup_logging()
    bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()

    print(config.DATABASE_URL)
    # Инициализация подключения к PostgreSQL
    await init_db(config.DATABASE_URL)

    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(contract_router)

    # Установка команд бота
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота и увидеть меню")
    ])

    # Запуск HTTP сервера для уведомлений
    http_server_host = getattr(config, 'HTTP_SERVER_HOST', '0.0.0.0')
    http_server_port = getattr(config, 'HTTP_SERVER_PORT', 8080)
    http_server_task = asyncio.create_task(start_http_server(bot, http_server_host, http_server_port))

    # Запуск polling
    try:
        await dp.start_polling(bot)
    finally:
        if http_server_task:
            http_server_task.cancel()
            try:
                await http_server_task
            except asyncio.CancelledError:
                logging.info("HTTP сервер успешно отменен.")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())