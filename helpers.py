import html
import re
from pathlib import Path
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaAnimation, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from emoji import E, em
import config

COLOR_NAMES_RU = {
    "черный": "000000",
    "чёрный": "000000",
    "белый": "FFFFFF",
    "серый": "808080",
    "графит": "141414",
    "сталь": "262626",
    "серебро": "C0C0C0",
    "красный": "FF3B30",
    "алый": "E63946",
    "синий": "007AFF",
    "голубой": "5AC8FA",
    "зеленый": "34C759",
    "зелёный": "34C759",
    "лайм": "39FF14",
    "мята": "D0F4DE",
    "желтый": "FFCC00",
    "жёлтый": "FFCC00",
    "оранжевый": "FF9500",
    "фиолетовый": "7209B7",
    "розовый": "FFB5A7",
    "лаванда": "C8B6FF",
    "бирюзовый": "00F0FF",
    "бирюза": "00F0FF",
    "золотой": "FFD700",
    "золото": "FFD700",
    "пурпур": "9D00FF",
    "неон": "39FF14",
}


def parse_color_input(text: str) -> str | None:
    t = text.strip().lower()
    if t in COLOR_NAMES_RU:
        return COLOR_NAMES_RU[t]
    clean = t.replace("#", "").upper()
    if len(clean) == 3 and re.fullmatch(r"[0-9A-F]{3}", clean):
        return "".join([c * 2 for c in clean])
    if len(clean) == 6 and re.fullmatch(r"[0-9A-F]{6}", clean):
        return clean
    return None


def format_main_menu_text(settings: dict) -> str:
    bg_style_map = {
        "solid": "Сплошной",
        "silk": "Студийный шёлк",
        "grid": "3D Сетка",
        "grain": "Плёночное зерно",
        "topo": "Топо-линии",
        "particles": "Парящие частицы",
        "spotlight": "Студийный софит",
        "scanline": "Кибер-сканлайн",
        "rain": "Капли дождя",
        "custom": "Своя медиа",
    }
    bg_style = settings.get("bg_style", "solid")
    color_hex = settings.get("bg_color", "000000")
    if bg_style == "solid":
        bg_str = f"#{color_hex}"
    elif bg_style == "custom":
        bg_str = "Своя медиа"
    else:
        style_name = bg_style_map.get(bg_style, "3D")
        bg_str = f"{style_name} (#{color_hex})" if color_hex != "000000" else style_name
    bg_str = html.escape(bg_str)

    recolor = settings.get("emoji_color")
    recolor_str = html.escape(f"#{recolor}" if recolor else "Оригинал")

    shadow = "Вкл" if settings.get("shadow_3d", 1) else "Выкл"
    wm = settings.get("watermark_text")
    wm_str = html.escape(wm) if wm else "Выкл"

    width = settings.get("width", 1920)
    height = settings.get("height", 530)
    scale = settings.get("emoji_scale", 100)

    return (
        f"{em(E.FIRE)} <b>GIF THE MY BOT · 60 FPS MOTION</b>\n"
        f"<i>Генератор живых широкоформатных баннеров</i>\n\n"
        f"{em(E.LIGHTNING)} <b>Отправь мне:</b>\n"
        f"<blockquote>Стикер (WEBM/TGS), строку премиум эмодзи или ссылку на стикерпак.</blockquote>\n\n"
        f"{em(E.SETTINGS)} <b>Конфигурация:</b>\n"
        f"<blockquote>"
        f"{em(E.BRUSH)} <b>Цвет фона:</b> <code>{bg_str}</code>\n"
        f"{em(E.RESIZE)} <b>Разрешение:</b> <code>{width}×{height}</code> · <b>60 FPS</b>\n"
        f"{em(E.DESIGN)} <b>ЦветEmoji:</b> <code>{recolor_str}</code>\n"
        f"{em(E.APPS)} <b>3D Фон:</b> <code>{shadow}</code>\n"
        f"{em(E.SCALE)} <b>Размер эмодзи:</b> <code>{scale}%</code>\n"
        f"{em(E.EDIT)} <b>Водяной знак:</b> <code>{wm_str}</code>"
        f"</blockquote>"
    )


def strip_icons(markup: InlineKeyboardMarkup | None) -> InlineKeyboardMarkup | None:
    if markup is None:
        return None
    rows = []
    for row in markup.inline_keyboard:
        fresh = []
        for btn in row:
            data = btn.model_dump(exclude_none=True)
            data.pop("icon_custom_emoji_id", None)
            data.pop("style", None)
            fresh.append(InlineKeyboardButton(**data))
        rows.append(fresh)
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def show_or_edit_banner(
    event: Message | CallbackQuery,
    banner_path: Path,
    cache_key: str,
    caption: str,
    reply_markup=None,
    parse_mode: str = "HTML",
) -> None:
    cached_id = config.get_cached_file_id(cache_key)

    if isinstance(event, CallbackQuery):
        msg = event.message
        if not msg:
            return

        if msg.animation or msg.video or msg.photo:
            media_input = cached_id or FSInputFile(banner_path)
            media = InputMediaAnimation(media=media_input, caption=caption, parse_mode=parse_mode)
            try:
                sent = await msg.edit_media(media=media, reply_markup=reply_markup)
                if hasattr(sent, "animation") and sent.animation and not cached_id:
                    config.save_cached_file_id(cache_key, sent.animation.file_id)
                return
            except TelegramBadRequest as e:
                err_text = str(e).lower()
                if "message is not modified" in err_text:
                    return
                if "icon" in err_text or "custom emoji" in err_text or "emoji_id" in err_text or "style" in err_text:
                    try:
                        sent = await msg.edit_media(media=media, reply_markup=strip_icons(reply_markup))
                        return
                    except Exception:
                        pass
                if cached_id:
                    try:
                        media = InputMediaAnimation(media=FSInputFile(banner_path), caption=caption, parse_mode=parse_mode)
                        sent = await msg.edit_media(media=media, reply_markup=reply_markup)
                        if hasattr(sent, "animation") and sent.animation:
                            config.save_cached_file_id(cache_key, sent.animation.file_id)
                        return
                    except TelegramBadRequest as e2:
                        if "message is not modified" in str(e2).lower():
                            return
            except Exception:
                pass

        try:
            await msg.delete()
        except Exception:
            pass

        media_input = cached_id or FSInputFile(banner_path)
        try:
            sent = await msg.answer_animation(
                animation=media_input,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            if sent.animation and not cached_id:
                config.save_cached_file_id(cache_key, sent.animation.file_id)
            return
        except TelegramBadRequest as e:
            err_text = str(e).lower()
            if "icon" in err_text or "custom emoji" in err_text or "emoji_id" in err_text or "style" in err_text:
                try:
                    sent = await msg.answer_animation(
                        animation=media_input,
                        caption=caption,
                        reply_markup=strip_icons(reply_markup),
                        parse_mode=parse_mode,
                    )
                    return
                except Exception:
                    pass
        except Exception:
            try:
                sent = await msg.answer_animation(
                    animation=FSInputFile(banner_path),
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )
                if sent.animation:
                    config.save_cached_file_id(cache_key, sent.animation.file_id)
                return
            except Exception:
                pass

        # Fallback to plain text if animation cannot be sent
        try:
            await msg.answer(text=caption, reply_markup=reply_markup, parse_mode=parse_mode)
            return
        except TelegramBadRequest as e:
            if "icon" in str(e).lower() or "custom emoji" in str(e).lower():
                try:
                    await msg.answer(text=caption, reply_markup=strip_icons(reply_markup), parse_mode=parse_mode)
                    return
                except Exception:
                    pass
        except Exception:
            pass

    elif isinstance(event, Message):
        media_input = cached_id or FSInputFile(banner_path)
        try:
            sent = await event.answer_animation(
                animation=media_input,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            if sent.animation and not cached_id:
                config.save_cached_file_id(cache_key, sent.animation.file_id)
            return
        except TelegramBadRequest as e:
            err_text = str(e).lower()
            if "icon" in err_text or "custom emoji" in err_text or "emoji_id" in err_text or "style" in err_text:
                try:
                    sent = await event.answer_animation(
                        animation=media_input,
                        caption=caption,
                        reply_markup=strip_icons(reply_markup),
                        parse_mode=parse_mode,
                    )
                    return
                except Exception:
                    pass
        except Exception:
            try:
                sent = await event.answer_animation(
                    animation=FSInputFile(banner_path),
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )
                if sent.animation:
                    config.save_cached_file_id(cache_key, sent.animation.file_id)
                return
            except Exception:
                pass

        # Fallback to plain text if animation cannot be sent
        try:
            await event.answer(text=caption, reply_markup=reply_markup, parse_mode=parse_mode)
            return
        except TelegramBadRequest as e:
            if "icon" in str(e).lower() or "custom emoji" in str(e).lower():
                try:
                    await event.answer(text=caption, reply_markup=strip_icons(reply_markup), parse_mode=parse_mode)
                    return
                except Exception:
                    pass
        except Exception:
            pass


def format_subscription_required_text(channel_name: str = "gifthemy") -> str:
    return (
        f"<b>{em(E.LINK)} ТРЕБУЕТСЯ ПОДПИСКА НА КАНАЛ</b>\n"
        f"<i>Для доступа ко всем функциям бота подпишитесь на наш канал</i>\n\n"
        f"<b>Зачем подписываться:</b>\n"
        f"<blockquote>"
        f"В канале @{channel_name} публикуются обновления, новые пресеты 60 FPS сцен, анонсы и поддержка."
        f"</blockquote>\n\n"
        f"<b>Как продолжить:</b>\n"
        f"<blockquote>"
        f"1. Нажмите кнопку «Подписаться на канал» ниже.\n"
        f"2. После подписки нажмите «Проверить подписку»."
        f"</blockquote>"
    )


