import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

import config
from helpers import format_subscription_required_text, show_or_edit_banner
from keyboards import get_subscription_kb
from services.subscription import check_user_subscription

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """Middleware для обязательной проверки подписки на канал."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if not user or user.is_bot:
            return await handler(event, data)

        # Разрешаем нажатие на кнопку «Проверить подписку»
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        is_sub = await check_user_subscription(bot, user.id)
        if is_sub:
            return await handler(event, data)

        text = format_subscription_required_text(config.CHANNEL_USERNAME)
        kb = get_subscription_kb(config.CHANNEL_URL)

        if isinstance(event, CallbackQuery):
            await event.answer("Для использования бота необходимо подписаться на канал!", show_alert=True)
            await show_or_edit_banner(
                event=event,
                banner_path=config.BANNER_MENU_PATH,
                cache_key="menu_main",
                caption=text,
                reply_markup=kb,
            )
            return

        if isinstance(event, Message):
            await show_or_edit_banner(
                event=event,
                banner_path=config.BANNER_MENU_PATH,
                cache_key="menu_main",
                caption=text,
                reply_markup=kb,
            )
            return

        return
