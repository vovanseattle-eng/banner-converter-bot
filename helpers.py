import html
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
        f"{em(E.FIRE)} <b>STUDIO BANNER · 60 FPS MOTION</b>\n"
        f"<i>Рендер широкоформатных живых медиа для ботов и каналов</i>\n\n"
        f"{em(E.SEND)} <b>Входной поток:</b>\n"
        f"<blockquote>Отправь стикер (WEBM/TGS), строку премиум эмодзи или ссылку на пак — бот соберёт 60 FPS баннер.</blockquote>\n\n"
        f"{em(E.SETTINGS)} <b>Параметры сцены:</b>\n"
        f"<blockquote>"
        f"{em(E.BRUSH)} <b>Холст:</b> <code>{bg_str}</code>\n"
        f"{em(E.RESIZE)} <b>Рендер:</b> <code>{width}×{height}</code> · <b>60 FPS</b>\n"
        f"{em(E.MEDIA)} <b>Формат:</b> <code>GIF (MP4)</code>\n"
        f"{em(E.DESIGN)} <b>Оттенок эмодзи:</b> <code>{recolor_str}</code>\n"
        f"{em(E.APPS)} <b>3D Тень:</b> <code>{shadow}</code> · <b>Масштаб:</b> <code>{scale}%</code>\n"
        f"{em(E.EDIT)} <b>Вотермарка:</b> <code>{wm_str}</code>"
        f"</blockquote>"
    )
