import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, PROXY_URL
from database import init_db
from handlers import menu, settings, recolor, watermark, presets, media_bg, convert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не указан в .env файле!")
        return

    await init_db()
    logger.info("База данных инициализирована.")

    # Прокси сессия для надежности при блокировках Telegram Bot API
    session = None
    if PROXY_URL:
        try:
            session = AiohttpSession(proxy=PROXY_URL)
            logger.info(f"Используется прокси: {PROXY_URL}")
        except Exception as e:
            logger.warning(f"Ошибка настройки прокси: {e}")

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключение обработчиков
    dp.include_router(menu.router)
    dp.include_router(settings.router)
    dp.include_router(recolor.router)
    dp.include_router(watermark.router)
    dp.include_router(presets.router)
    dp.include_router(media_bg.router)
    dp.include_router(convert.router)

    logger.info("Запуск Telegram-бота конвертера баннеров 60 FPS...")

    # Цикл с автоматическим перезапуском при разрывах соединения/VPN
    while True:
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
        except Exception as e:
            logger.warning(f"Соединение прервано: {e}. Переподключение через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
