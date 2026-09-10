from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import WEBAPP_COLOR_PICKER_URL
from emoji import E

DANGER = "danger"


def _b(
    builder: InlineKeyboardBuilder,
    text: str,
    data: str | None = None,
    icon: E | None = None,
    *,
    style: str | None = None,
    url: str | None = None,
    web_app: WebAppInfo | None = None,
) -> None:
    builder.button(
        text=text,
        callback_data=data if (not url and not web_app) else None,
        url=url,
        web_app=web_app,
        icon_custom_emoji_id=icon,
        style=style,
    )


def _back(builder: InlineKeyboardBuilder, text: str = "Назад", data: str = "back_to_main") -> None:
    # Без стрелок/смайликов в тексте, только кастомная иконка E.BACK
    _b(builder, text, data, E.BACK)


def get_main_menu_kb(settings: dict) -> InlineKeyboardMarkup:
    """
    Главное меню:
    - Главные действия (Цвет фона, 3D Фон) на всю ширину и в огненно-красном стиле DANGER.
    - Второстепенные настройки сгруппированы по 2 в строке.
    - Своя медиа внизу на отдельной строке.
    """
    b = InlineKeyboardBuilder()
    _b(b, "Цвет фона", "menu:color", E.BRUSH, style=DANGER)
    _b(b, "3D Фон", "menu:bg3d", E.APPS, style=DANGER)
    _b(b, "Разрешение", "menu:resolution", E.RESIZE)
    _b(b, "ЦветEmoji", "menu:recolor", E.DESIGN)
    _b(b, "Размер эмодзи", "menu:scale", E.SCALE)
    _b(b, "Водяной знак", "menu:watermark", E.EDIT)
    _b(b, "Своя медиа", "menu:media", E.MEDIA)
    b.adjust(1, 1, 2, 2, 1)
    return b.as_markup()


COLOR_PALETTES = {
    "classic": {
        "title": "Классика",
        "colors": [
            ("Черный", "000000"),
            ("Графит", "141414"),
            ("Сталь", "262626"),
            ("Серый", "808080"),
            ("Серебро", "C0C0C0"),
            ("Белый", "FFFFFF"),
        ],
    },
    "vibrant": {
        "title": "Яркие",
        "colors": [
            ("Красный", "FF3B30"),
            ("Оранжевый", "FF9500"),
            ("Желтый", "FFCC00"),
            ("Зеленый", "34C759"),
            ("Синий", "007AFF"),
            ("Фиолетовый", "7209B7"),
        ],
    },
    "pastel": {
        "title": "Пастель",
        "colors": [
            ("Лаванда", "C8B6FF"),
            ("Небесный", "B8C0FF"),
            ("Мята", "D0F4DE"),
            ("Персик", "FFD8BE"),
            ("Розовый", "FFB5A7"),
            ("Крем", "ECE4DB"),
        ],
    },
    "neon": {
        "title": "Неон",
        "colors": [
            ("Неон-лайм", "39FF14"),
            ("Кибер-бирюза", "00F0FF"),
            ("Электрик", "0038FF"),
            ("Неон-розовый", "FF007F"),
            ("Пурпур", "9D00FF"),
            ("Золото", "FFD700"),
        ],
    },
}


def build_color_picker_kb(target: str, active_cat: str = "classic", has_extra: bool = False) -> InlineKeyboardMarkup:
    if active_cat not in COLOR_PALETTES:
        active_cat = "classic"

    b = InlineKeyboardBuilder()
    # Вкладки палитр
    for cat_key, cat_data in COLOR_PALETTES.items():
        title = ("• " if cat_key == active_cat else "") + cat_data["title"]
        _b(b, title, f"pal_cat:{target}:{cat_key}")

    # Цвета
    colors = COLOR_PALETTES[active_cat]["colors"]
    prefix = {
        "bg": "set_color",
        "recolor": "set_recolor",
        "wm": "set_wmcolor",
    }.get(target, "set_color")

    for name, code in colors:
        _b(b, f"{name} (#{code})", f"{prefix}:{code}")

    # Дополнительные кнопки
    extra_count = 0
    if target == "recolor" and has_extra:
        _b(b, "Убрать цвет (оригинал)", "clear_recolor", E.TRASH)
        extra_count += 1

    # Главное действие: открыть спектр-палитру WebApp (акцентный стиль DANGER)
    _b(
        b,
        "Спектр-палитра (любой оттенок)",
        web_app=WebAppInfo(url=WEBAPP_COLOR_PICKER_URL),
        icon=E.DESIGN,
        style=DANGER,
    )
    extra_count += 1

    back_target = "menu:watermark" if target == "wm" else "back_to_main"
    _back(b, "Назад", back_target)
    extra_count += 1

    adjustments = [4] + [2] * (len(colors) // 2) + [1] * extra_count
    b.adjust(*adjustments)
    return b.as_markup()


def get_color_kb(active_cat: str = "classic") -> InlineKeyboardMarkup:
    return build_color_picker_kb(target="bg", active_cat=active_cat)


def get_resolution_kb() -> InlineKeyboardMarkup:
    """Разрешения: основной баннер 1920x530 выделен и на всю ширину."""
    b = InlineKeyboardBuilder()
    _b(b, "1920x530 (Баннер)", "set_res:1920x530", E.RESIZE, style=DANGER)
    _b(b, "1920x600", "set_res:1920x600")
    _b(b, "1280x720 (16:9)", "set_res:1280x720")
    _b(b, "1080x1080 (1:1)", "set_res:1080x1080")
    _b(b, "1080x1920 (9:16)", "set_res:1080x1920")
    _back(b, "Назад", "back_to_main")
    b.adjust(1, 2, 2, 1)
    return b.as_markup()


def get_bg3d_kb(current_style: str, shadow_on: bool) -> InlineKeyboardMarkup:
    shadow_text = "3D Тень: ВКЛ" if shadow_on else "3D Тень: ВЫКЛ"
    b = InlineKeyboardBuilder()
    styles = [
        ("solid", "Сплошной цвет"),
        ("silk", "Студийный шёлк"),
        ("grid", "3D Сетка"),
        ("grain", "Плёночное зерно"),
        ("topo", "Топо-линии"),
        ("particles", "Парящие частицы"),
        ("spotlight", "Студийный софит"),
        ("scanline", "Кибер-сканлайн"),
    ]
    for key, name in styles:
        prefix = "✓ " if current_style == key else ""
        _b(b, f"{prefix}{name}", f"set_bgstyle:{key}")

    rain_prefix = "✓ " if current_style == "rain" else ""
    _b(b, f"{rain_prefix}Капли дождя", "set_bgstyle:rain")
    _b(b, shadow_text, "toggle_shadow", E.CHECK if shadow_on else E.CROSS)
    _back(b, "Назад", "back_to_main")
    b.adjust(2, 2, 2, 2, 1, 1, 1)
    return b.as_markup()


def get_recolor_kb(has_color: bool, active_cat: str = "classic") -> InlineKeyboardMarkup:
    return build_color_picker_kb(target="recolor", active_cat=active_cat, has_extra=has_color)


def get_media_kb(has_custom: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    _b(b, "Загрузить медиа", "upload_media", E.SEND, style=DANGER)
    if has_custom:
        _b(b, "Сбросить свой фон", "reset_media", E.TRASH)
    _back(b, "Назад", "back_to_main")
    b.adjust(*([1] * (3 if has_custom else 2)))
    return b.as_markup()


def get_watermark_kb(has_wm: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    _b(b, "Название", "wm:title", E.EDIT)
    _b(b, "Цвет", "wm:color", E.BRUSH)
    _b(b, "Позиция", "wm:pos", E.RESIZE)
    if has_wm:
        _b(b, "Отключить водяной знак", "wm:clear", E.TRASH)
    _back(b, "Назад", "back_to_main")
    if has_wm:
        b.adjust(2, 1, 1, 1)
    else:
        b.adjust(2, 1, 1)
    return b.as_markup()


def get_wm_color_kb(active_cat: str = "classic") -> InlineKeyboardMarkup:
    return build_color_picker_kb(target="wm", active_cat=active_cat)


def get_scale_kb(current_scale: int) -> InlineKeyboardMarkup:
    scales = [50, 75, 100, 125, 150, 200]
    b = InlineKeyboardBuilder()
    for s in scales:
        label = f"✓ {s}%" if s == current_scale else f"{s}%"
        _b(b, label, f"set_scale:{s}")
    _back(b, "Назад", "back_to_main")
    b.adjust(3, 3, 1)
    return b.as_markup()


def get_result_kb(result_filename: str) -> InlineKeyboardMarkup:
    """Экран готового результата: скачать файлом — крупная акцентная кнопка DANGER."""
    b = InlineKeyboardBuilder()
    _b(b, "Скачать файлом без сжатия", f"send_doc:{result_filename}", E.DOWNLOAD, style=DANGER)
    _b(b, "Настройки", "result:settings", E.SETTINGS)
    b.adjust(1, 1)
    return b.as_markup()
