import re
from emoji import E, em

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
    bg_str = bg_style_map.get(settings.get("bg_style", "solid"), "Сплошной")

    recolor = settings.get("emoji_color")
    recolor_str = f"#{recolor}" if recolor else "Оригинал"

    shadow = "Вкл" if settings.get("shadow_3d", 1) else "Выкл"
    wm = settings.get("watermark_text")
    wm_str = wm if wm else "Выкл"

    return (
        f"{em(E.BRUSH)} <b>Цвет фона:</b> {bg_str}\n"
        f"{em(E.RESIZE)} <b>Разрешение:</b> {settings.get('width', 1920)}x{settings.get('height', 530)}\n"
        f"{em(E.RESIZE)} <b>Размер эмодзи:</b> {settings.get('emoji_scale', 100)}%\n"
        f"{em(E.BRUSH)} <b>ЦветEmoji:</b> {recolor_str}\n"
        f"{em(E.APPS)} <b>3D Тень:</b> {shadow}\n"
        f"{em(E.EDIT)} <b>Вотермарка:</b> {wm_str}\n\n"
        f"<b>Отправь мне emoji или sticker</b> (можно паком или ссылку)"
    )
