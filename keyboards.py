from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from emoji import E
from config import WEBAPP_COLOR_PICKER_URL


def get_main_menu_kb(settings: dict) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="Цвет фона", callback_data="menu:color", icon_custom_emoji_id=E.BRUSH),
            InlineKeyboardButton(text="Разрешение", callback_data="menu:resolution", icon_custom_emoji_id=E.RESIZE),
        ],
        [
            InlineKeyboardButton(text="3D Фон", callback_data="menu:bg3d", icon_custom_emoji_id=E.APPS),
            InlineKeyboardButton(text="ЦветEmoji", callback_data="menu:recolor", icon_custom_emoji_id=E.DESIGN),
        ],
        [
            InlineKeyboardButton(text="Своя медиа", callback_data="menu:media", icon_custom_emoji_id=E.MEDIA),
            InlineKeyboardButton(text="Заметки", callback_data="menu:presets", icon_custom_emoji_id=E.FILE),
        ],
        [
            InlineKeyboardButton(text="Водяной знак", callback_data="menu:watermark", icon_custom_emoji_id=E.EDIT),
            InlineKeyboardButton(text="Размер эмодзи", callback_data="menu:scale", icon_custom_emoji_id=E.SCALE),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


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

    tabs_row = []
    for cat_key, cat_data in COLOR_PALETTES.items():
        title = ("• " if cat_key == active_cat else "") + cat_data["title"]
        tabs_row.append(
            InlineKeyboardButton(text=title, callback_data=f"pal_cat:{target}:{cat_key}")
        )

    color_rows = []
    colors = COLOR_PALETTES[active_cat]["colors"]
    prefix = {
        "bg": "set_color",
        "recolor": "set_recolor",
        "wm": "set_wmcolor",
    }.get(target, "set_color")

    for i in range(0, len(colors), 2):
        pair = colors[i : i + 2]
        row = [
            InlineKeyboardButton(text=f"{name} (#{code})", callback_data=f"{prefix}:{code}")
            for name, code in pair
        ]
        color_rows.append(row)

    extra_rows = []
    if target == "recolor" and has_extra:
        extra_rows.append([
            InlineKeyboardButton(
                text="Убрать цвет (оригинал)", callback_data="clear_recolor", icon_custom_emoji_id=E.TRASH
            )
        ])

    extra_rows.append([
        InlineKeyboardButton(
            text="Спектр-палитра (любой оттенок)",
            web_app=WebAppInfo(url=WEBAPP_COLOR_PICKER_URL),
        )
    ])

    back_target = "menu:watermark" if target == "wm" else "back_to_main"
    extra_rows.append([
        InlineKeyboardButton(text="◁ Назад", callback_data=back_target, icon_custom_emoji_id=E.BACK)
    ])

    return InlineKeyboardMarkup(inline_keyboard=[tabs_row, *color_rows, *extra_rows])


def get_color_kb(active_cat: str = "classic") -> InlineKeyboardMarkup:
    return build_color_picker_kb(target="bg", active_cat=active_cat)


def get_resolution_kb() -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="1920x530 (Баннер)", callback_data="set_res:1920x530"),
            InlineKeyboardButton(text="1920x600", callback_data="set_res:1920x600"),
        ],
        [
            InlineKeyboardButton(text="1280x720 (16:9)", callback_data="set_res:1280x720"),
            InlineKeyboardButton(text="1080x1080 (1:1)", callback_data="set_res:1080x1080"),
        ],
        [
            InlineKeyboardButton(text="1080x1920 (9:16)", callback_data="set_res:1080x1920"),
        ],
        [InlineKeyboardButton(text="◁ Назад", callback_data="back_to_main", icon_custom_emoji_id=E.BACK)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_bg3d_kb(current_style: str, shadow_on: bool) -> InlineKeyboardMarkup:
    shadow_text = "3D Тень: ВКЛ" if shadow_on else "3D Тень: ВЫКЛ"
    kb = [
        [
            InlineKeyboardButton(text=("✓ " if current_style == "solid" else "") + "Сплошной цвет", callback_data="set_bgstyle:solid"),
            InlineKeyboardButton(text=("✓ " if current_style == "silk" else "") + "Студийный шёлк", callback_data="set_bgstyle:silk"),
        ],
        [
            InlineKeyboardButton(text=("✓ " if current_style == "grid" else "") + "3D Сетка", callback_data="set_bgstyle:grid"),
            InlineKeyboardButton(text=("✓ " if current_style == "grain" else "") + "Плёночное зерно", callback_data="set_bgstyle:grain"),
        ],
        [
            InlineKeyboardButton(text=("✓ " if current_style == "topo" else "") + "Топо-линии", callback_data="set_bgstyle:topo"),
            InlineKeyboardButton(text=("✓ " if current_style == "particles" else "") + "Парящие частицы", callback_data="set_bgstyle:particles"),
        ],
        [
            InlineKeyboardButton(text=("✓ " if current_style == "spotlight" else "") + "Студийный софит", callback_data="set_bgstyle:spotlight"),
            InlineKeyboardButton(text=("✓ " if current_style == "scanline" else "") + "Кибер-сканлайн", callback_data="set_bgstyle:scanline"),
        ],
        [
            InlineKeyboardButton(text=("✓ " if current_style == "rain" else "") + "Капли дождя", callback_data="set_bgstyle:rain"),
        ],
        [
            InlineKeyboardButton(text=shadow_text, callback_data="toggle_shadow", icon_custom_emoji_id=E.CHECK if shadow_on else E.CROSS),
        ],
        [InlineKeyboardButton(text="◁ Назад", callback_data="back_to_main", icon_custom_emoji_id=E.BACK)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_recolor_kb(has_color: bool, active_cat: str = "classic") -> InlineKeyboardMarkup:
    return build_color_picker_kb(target="recolor", active_cat=active_cat, has_extra=has_color)


def get_media_kb(has_custom: bool) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="Загрузить медиа", callback_data="upload_media", icon_custom_emoji_id=E.SEND)],
    ]
    if has_custom:
        kb.append([InlineKeyboardButton(text="Сбросить свой фон", callback_data="reset_media", icon_custom_emoji_id=E.TRASH)])
    kb.append([InlineKeyboardButton(text="◁ Назад", callback_data="back_to_main", icon_custom_emoji_id=E.BACK)])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_presets_kb(presets: list) -> InlineKeyboardMarkup:
    kb = []
    for p in presets[:5]:
        kb.append([
            InlineKeyboardButton(text=p['name'], callback_data=f"load_preset:{p['id']}", icon_custom_emoji_id=E.FILE),
            InlineKeyboardButton(text="Удалить", callback_data=f"del_preset:{p['id']}", icon_custom_emoji_id=E.CROSS),
        ])
    kb.append([InlineKeyboardButton(text="Новая заметка", callback_data="new_preset", icon_custom_emoji_id=E.EDIT)])
    kb.append([InlineKeyboardButton(text="◁ Назад", callback_data="back_to_main", icon_custom_emoji_id=E.BACK)])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_watermark_kb(has_wm: bool) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="Название", callback_data="wm:title", icon_custom_emoji_id=E.EDIT),
            InlineKeyboardButton(text="Цвет", callback_data="wm:color", icon_custom_emoji_id=E.BRUSH),
        ],
        [
            InlineKeyboardButton(text="Позиция", callback_data="wm:pos", icon_custom_emoji_id=E.RESIZE),
        ],
    ]
    if has_wm:
        kb.append([InlineKeyboardButton(text="Отключить водяной знак", callback_data="wm:clear", icon_custom_emoji_id=E.TRASH)])
    kb.append([InlineKeyboardButton(text="◁ Назад", callback_data="back_to_main", icon_custom_emoji_id=E.BACK)])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_wm_color_kb(active_cat: str = "classic") -> InlineKeyboardMarkup:
    return build_color_picker_kb(target="wm", active_cat=active_cat)


def get_scale_kb(current_scale: int) -> InlineKeyboardMarkup:
    scales = [50, 75, 100, 125, 150, 200]
    row1 = []
    row2 = []
    for s in scales[:3]:
        label = f"✓ {s}%" if s == current_scale else f"{s}%"
        row1.append(InlineKeyboardButton(text=label, callback_data=f"set_scale:{s}"))
    for s in scales[3:]:
        label = f"✓ {s}%" if s == current_scale else f"{s}%"
        row2.append(InlineKeyboardButton(text=label, callback_data=f"set_scale:{s}"))

    return InlineKeyboardMarkup(
        inline_keyboard=[row1, row2, [InlineKeyboardButton(text="◁ Назад", callback_data="back_to_main", icon_custom_emoji_id=E.BACK)]]
    )


def get_result_kb(result_filename: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Скачать файлом без сжатия",
                    callback_data=f"send_doc:{result_filename}",
                    icon_custom_emoji_id=E.DOWNLOAD,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Настройки",
                    callback_data="back_to_main",
                    icon_custom_emoji_id=E.SETTINGS,
                )
            ],
        ]
    )
