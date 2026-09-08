import html
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_user_settings, update_user_field
from keyboards import get_watermark_kb, get_main_menu_kb, get_wm_color_kb
from helpers import format_main_menu_text, parse_color_input
from states import SettingsStates
from emoji import E, em, title

router = Router()


@router.callback_query(F.data == "menu:watermark")
async def cb_watermark_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    wm = settings.get("watermark_text")
    if wm:
        pos_names = {
            "bottom_right": "Снизу справа",
            "bottom_left": "Снизу слева",
            "top_right": "Сверху справа",
            "top_left": "Сверху слева",
            "center": "По центру",
        }
        pos_str = pos_names.get(settings.get("watermark_pos"), "Снизу справа")
        text = (
            f"{title(E.EDIT, 'Вотермарка')}\n\n"
            f"<blockquote>Текст: <code>{html.escape(wm)}</code>\n"
            f"Цвет: <code>#{settings.get('watermark_color', 'FFFFFF')}</code>\n"
            f"Позиция: {pos_str}</blockquote>"
        )
    else:
        text = (
            f"{title(E.EDIT, 'Вотермарка')}\n\n"
            f"<blockquote>Статус: <code>Выключена</code>\n"
            f"Укажи название или канал, чтобы включить подпись на баннерах.</blockquote>"
        )

    await callback.message.edit_text(text, reply_markup=get_watermark_kb(bool(wm)), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "wm:title")
async def cb_wm_title(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_wm_text)
    await callback.message.edit_text(
        f"{title(E.EDIT, 'Введи текст вотермарки')} (до 30 символов):\n"
        "Например: <code>@my_channel</code> или имя проекта",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.waiting_wm_text)
async def msg_wm_title(message: Message, state: FSMContext):
    val = message.text.strip()[:30]
    await update_user_field(message.from_user.id, "watermark_text", val)
    await state.clear()
    settings = await get_user_settings(message.from_user.id)
    await message.answer(
        f"{em(E.CHECK)} <b>Вотермарка установлена:</b> <code>{val}</code>\n\n" + format_main_menu_text(settings),
        reply_markup=get_main_menu_kb(settings),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "wm:color")
async def cb_wm_color(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_wm_color)
    text = (
        f"{title(E.BRUSH, 'Цвет вотермарки')}\n\n"
        "Выбери оттенок в 1 клик по вкладкам ниже, либо напиши название (например: <code>белый</code>, <code>золото</code>, <code>серебро</code>).\n\n"
        "Также можно открыть спектр-палитру или отправить HEX-код:"
    )
    await callback.message.edit_text(text, reply_markup=get_wm_color_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("set_wmcolor:"))
async def cb_set_wmcolor(callback: CallbackQuery, state: FSMContext):
    hex_color = callback.data.split(":")[1].upper()
    await update_user_field(callback.from_user.id, "watermark_color", hex_color)
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_text(
        format_main_menu_text(settings), reply_markup=get_main_menu_kb(settings), parse_mode="HTML"
    )
    await callback.answer(f"Цвет вотермарки: #{hex_color}")


@router.message(SettingsStates.waiting_wm_color)
async def msg_wm_color(message: Message, state: FSMContext):
    hex_val = parse_color_input(message.text)
    if hex_val:
        await update_user_field(message.from_user.id, "watermark_color", hex_val)
        await state.clear()
        settings = await get_user_settings(message.from_user.id)
        await message.answer(
            f"{em(E.CHECK)} <b>Цвет вотермарки:</b> <code>#{hex_val}</code>\n\n" + format_main_menu_text(settings),
            reply_markup=get_main_menu_kb(settings),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"{em(E.CROSS)} Не удалось распознать цвет. Выбери кнопку из палитры, отправь HEX (например <code>FFFFFF</code>) или напиши название (<code>белый</code>, <code>золото</code>):",
            parse_mode="HTML",
        )


@router.callback_query(F.data == "wm:pos")
async def cb_wm_pos(callback: CallbackQuery):
    settings = await get_user_settings(callback.from_user.id)
    cur = settings.get("watermark_pos", "bottom_right")
    order = ["bottom_right", "bottom_left", "center", "top_right"]
    next_pos = order[(order.index(cur) + 1) % len(order)]
    await update_user_field(callback.from_user.id, "watermark_pos", next_pos)
    await callback.answer(f"Позиция: {next_pos}")
    settings["watermark_pos"] = next_pos
    wm = settings.get("watermark_text")
    text = (
        f"{title(E.EDIT, 'Вотермарка активна:')} <code>{wm}</code>\n"
        f"Цвет: <code>#{settings.get('watermark_color', 'FFFFFF')}</code>\n"
        f"Позиция: <b>{next_pos}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_watermark_kb(bool(wm)), parse_mode="HTML")


@router.callback_query(F.data == "wm:clear")
async def cb_wm_clear(callback: CallbackQuery, state: FSMContext):
    await update_user_field(callback.from_user.id, "watermark_text", None)
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_text(
        format_main_menu_text(settings), reply_markup=get_main_menu_kb(settings), parse_mode="HTML"
    )
    await callback.answer("Вотермарка отключена")
