import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_user_settings, update_user_field
from keyboards import (
    get_color_kb,
    get_recolor_kb,
    get_wm_color_kb,
    get_resolution_kb,
    get_bg3d_kb,
    get_scale_kb,
    get_main_menu_kb,
)
from helpers import format_main_menu_text, parse_color_input, show_or_edit_banner
from states import SettingsStates
from emoji import E, em, title
import config

router = Router()


# --- ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК ПАЛИТРЫ (1 КЛИК) ---
@router.callback_query(F.data.startswith("pal_cat:"))
async def cb_palette_category(callback: CallbackQuery):
    parts = callback.data.split(":")
    target = parts[1]
    cat_key = parts[2]
    settings = await get_user_settings(callback.from_user.id)
    has_color = bool(settings.get("emoji_color"))

    if target == "bg":
        kb = get_color_kb(active_cat=cat_key)
    elif target == "recolor":
        kb = get_recolor_kb(has_color=has_color, active_cat=cat_key)
    else:
        kb = get_wm_color_kb(active_cat=cat_key)

    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


# --- ЦВЕТ ФОНА ---
@router.callback_query(F.data == "menu:color")
async def cb_color_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_bg_color)
    settings = await get_user_settings(callback.from_user.id)
    curr_color = f"#{settings.get('bg_color', '000000')}"
    text = (
        f"{title(E.BRUSH, 'Цвет фона')}\n\n"
        f"<blockquote>Текущий: <code>{curr_color}</code>\n"
        f"Выбери оттенок в 1 клик по вкладкам ниже или отправь HEX / название (синий, графит, серебро, золото):</blockquote>"
    )
    await show_or_edit_banner(
        event=callback,
        banner_path=config.BANNER_COLOR_PATH,
        cache_key="menu_color",
        caption=text,
        reply_markup=get_color_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_color:"))
async def cb_set_color(callback: CallbackQuery, state: FSMContext):
    hex_color = callback.data.split(":")[1].upper()
    await update_user_field(callback.from_user.id, "bg_color", hex_color)
    await update_user_field(callback.from_user.id, "bg_style", "solid")
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    await show_or_edit_banner(
        event=callback,
        banner_path=config.BANNER_MENU_PATH,
        cache_key="menu_main",
        caption=format_main_menu_text(settings),
        reply_markup=get_main_menu_kb(settings),
    )
    await callback.answer(f"Цвет фона: #{hex_color}")


@router.message(SettingsStates.waiting_bg_color)
async def msg_bg_color(message: Message, state: FSMContext):
    hex_val = parse_color_input(message.text)
    if hex_val:
        await update_user_field(message.from_user.id, "bg_color", hex_val)
        await update_user_field(message.from_user.id, "bg_style", "solid")
        await state.clear()
        settings = await get_user_settings(message.from_user.id)
        await show_or_edit_banner(
            event=message,
            banner_path=config.BANNER_MENU_PATH,
            cache_key="menu_main",
            caption=f"{em(E.CHECK)} <b>Цвет фона установлен:</b> <code>#{hex_val}</code>\n\n" + format_main_menu_text(settings),
            reply_markup=get_main_menu_kb(settings),
        )
    else:
        await message.answer(
            f"{em(E.CROSS)} Не удалось распознать цвет. Выбери кнопку из палитры, отправь HEX (например <code>000000</code>) или напиши название (<code>синий</code>, <code>красный</code>, <code>черный</code>):",
            parse_mode="HTML",
        )


# --- РАЗРЕШЕНИЕ ---
@router.callback_query(F.data == "menu:resolution")
async def cb_res_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_resolution)
    settings = await get_user_settings(callback.from_user.id)
    curr_res = f"{settings.get('width', 1920)}×{settings.get('height', 530)}"
    text = (
        f"{title(E.RESIZE, 'Разрешение баннера')}\n\n"
        f"<blockquote>Текущее: <code>{curr_res}</code> · <b>60 FPS</b>\n"
        f"Выбери готовый формат ниже или отправь в чат (например <code>1920x530</code>):</blockquote>"
    )
    await show_or_edit_banner(
        event=callback,
        banner_path=config.BANNER_SETTINGS_PATH,
        cache_key="menu_settings",
        caption=text,
        reply_markup=get_resolution_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_res:"))
async def cb_set_resolution(callback: CallbackQuery, state: FSMContext):
    w, h = callback.data.split(":")[1].split("x")
    await update_user_field(callback.from_user.id, "width", int(w))
    await update_user_field(callback.from_user.id, "height", int(h))
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    await show_or_edit_banner(
        event=callback,
        banner_path=config.BANNER_MENU_PATH,
        cache_key="menu_main",
        caption=format_main_menu_text(settings),
        reply_markup=get_main_menu_kb(settings),
    )
    await callback.answer(f"Разрешение: {w}x{h}")


@router.message(SettingsStates.waiting_resolution)
async def msg_resolution(message: Message, state: FSMContext):
    match = re.fullmatch(r"(\d{3,4})[xXхХ*](\d{3,4})", message.text.strip())
    if match:
        w = int(match.group(1))
        h = int(match.group(2))
        if 300 <= w <= 2560 and 100 <= h <= 1440:
            await update_user_field(message.from_user.id, "width", w)
            await update_user_field(message.from_user.id, "height", h)
            await state.clear()
            settings = await get_user_settings(message.from_user.id)
            await show_or_edit_banner(
                event=message,
                banner_path=config.BANNER_MENU_PATH,
                cache_key="menu_main",
                caption=f"{em(E.CHECK)} <b>Разрешение установлено:</b> {w}x{h}\n\n" + format_main_menu_text(settings),
                reply_markup=get_main_menu_kb(settings),
            )
            return
    await message.answer(f"{em(E.CROSS)} Введи разрешение в формате <code>ШиринаxВысота</code> (например <code>1920x530</code>):", parse_mode="HTML")


# --- 3D ФОН И ЭФФЕКТЫ ---
@router.callback_query(F.data == "menu:bg3d")
async def cb_bg3d_menu(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    text = (
        f"{title(E.APPS, '3D Фон и Стили сцены')}\n\n"
        f"<blockquote>• <b>Сплошной цвет</b>: классический монохром\n"
        f"• <b>Студийный шёлк</b>: текучий рельеф жидкого металла\n"
        f"• <b>3D Сетка</b>: нео-бруталистская сетка\n"
        f"• <b>Капли дождя</b>: кинематографичный дождь\n"
        f"• <b>3D Тень</b>: эффект парения эмодзи над холстом</blockquote>"
    )
    await show_or_edit_banner(
        event=callback,
        banner_path=config.BANNER_SETTINGS_PATH,
        cache_key="menu_settings",
        caption=text,
        reply_markup=get_bg3d_kb(settings.get("bg_style", "solid"), bool(settings.get("shadow_3d", 1))),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_bgstyle:"))
async def cb_set_bgstyle(callback: CallbackQuery):
    style = callback.data.split(":")[1]
    await update_user_field(callback.from_user.id, "bg_style", style)
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=get_bg3d_kb(settings.get("bg_style", "solid"), bool(settings.get("shadow_3d", 1)))
    )
    names = {
        "solid": "Сплошной",
        "silk": "Студийный шёлк",
        "grid": "3D Сетка",
        "grain": "Плёночное зерно",
        "topo": "Топо-линии",
        "particles": "Парящие частицы",
        "spotlight": "Студийный софит",
        "scanline": "Кибер-сканлайн",
        "rain": "Капли дождя",
    }
    await callback.answer(f"Фон: {names.get(style, style)}")


@router.callback_query(F.data == "toggle_shadow")
async def cb_toggle_shadow(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    new_val = 0 if settings.get("shadow_3d", 1) else 1
    await update_user_field(callback.from_user.id, "shadow_3d", new_val)
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=get_bg3d_kb(settings.get("bg_style", "solid"), bool(new_val))
    )
    status = "включена" if new_val else "выключена"
    await callback.answer(f"3D Тень {status}")


# --- РАЗМЕР ЭМОДЗИ ---
@router.callback_query(F.data == "menu:scale")
async def cb_scale_menu(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    curr = settings.get("emoji_scale", 100)
    text = (
        f"{title(E.RESIZE, 'Размер эмодзи')}\n\n"
        f"<blockquote>Текущий масштаб: <code>{curr}%</code>\n"
        f"Выбери размер относительно высоты холста:</blockquote>"
    )
    await show_or_edit_banner(
        event=callback,
        banner_path=config.BANNER_SETTINGS_PATH,
        cache_key="menu_settings",
        caption=text,
        reply_markup=get_scale_kb(curr),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_scale:"))
async def cb_set_scale(callback: CallbackQuery):
    scale_val = int(callback.data.split(":")[1])
    await update_user_field(callback.from_user.id, "emoji_scale", scale_val)
    settings = await get_user_settings(callback.from_user.id)
    await show_or_edit_banner(
        event=callback,
        banner_path=config.BANNER_MENU_PATH,
        cache_key="menu_main",
        caption=format_main_menu_text(settings),
        reply_markup=get_main_menu_kb(settings),
    )
    await callback.answer(f"Размер: {scale_val}%")
