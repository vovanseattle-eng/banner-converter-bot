import html
import re
from pathlib import Path
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaAnimation
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
        "solid": f"#{settings.get('bg_color', '000000')}",
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
    bg_str = html.escape(bg_style_map.get(settings.get("bg_style", "solid"), "Сплошной"))

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
        except Exception:
            sent = await msg.answer_animation(
                animation=FSInputFile(banner_path),
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            if sent.animation:
                config.save_cached_file_id(cache_key, sent.animation.file_id)

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
        except Exception:
            sent = await event.answer_animation(
                animation=FSInputFile(banner_path),
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            if sent.animation:
                config.save_cached_file_id(cache_key, sent.animation.file_id)

