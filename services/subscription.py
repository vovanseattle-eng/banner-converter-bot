import logging
import time
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

import config

logger = logging.getLogger(__name__)

# Кэш подписок: user_id -> timestamp успешной проверки (TTL 120 сек)
_SUBSCRIBED_CACHE: dict[int, float] = {}
CACHE_TTL = 120.0


def clear_user_subscription_cache(user_id: int) -> None:
    _SUBSCRIBED_CACHE.pop(user_id, None)


async def check_user_subscription(bot: Bot, user_id: int) -> bool:
    if not config.CHANNEL_USERNAME:
        return True

    now = time.time()
    if user_id in _SUBSCRIBED_CACHE and (now - _SUBSCRIBED_CACHE[user_id]) < CACHE_TTL:
        return True

    channel = f"@{config.CHANNEL_USERNAME}"
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        if member.status in (
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        ):
            _SUBSCRIBED_CACHE[user_id] = now
            return True
        if member.status == ChatMemberStatus.RESTRICTED and getattr(member, "is_member", False):
            _SUBSCRIBED_CACHE[user_id] = now
            return True
        return False
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "user not found" in err or "participant_id_invalid" in err:
            return False
        logger.warning(f"Ошибка проверки подписки: {e}")
        return False
    except Exception as e:
        logger.warning(f"Неожиданная ошибка проверки подписки: {e}")
        return False
