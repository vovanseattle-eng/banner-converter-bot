import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_user_settings, update_user_field
from keyboards import get_recolor_kb, get_main_menu_kb
from helpers import format_main_menu_text, parse_color_input
from states import SettingsStates
from emoji import E, em, title

router = Router()


@router.callback_query(F.data == "menu:recolor")
async def cb_recolor_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_recolor)
    settings = await get_user_settings(callback.from_user.id)
    has_color = bool(settings.get("emoji_color"))
    recolor = settings.get("emoji_color")
    recolor_str = f"#{recolor}" if recolor else "Оригинал"
    text = (
        f"{title(E.BRUSH, 'Цвет Emoji / Стикера')}\n\n"
        f"<blockquote>Текущий: <code>{recolor_str}</code>\n"
        f"Выбери оттенок в 1 клик по вкладкам ниже или напиши в чат (сталь, серебро, золото, неон):</blockquote>"
    )
    await callback.message.edit_text(text, reply_markup=get_recolor_kb(has_color), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("set_recolor:"))
async def cb_set_recolor(callback: CallbackQuery, state: FSMContext):
    hex_color = callback.data.split(":")[1].upper()
    await update_user_field(callback.from_user.id, "emoji_color", hex_color)
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_text(
        format_main_menu_text(settings), reply_markup=get_main_menu_kb(settings), parse_mode="HTML"
    )
    await callback.answer(f"Цвет эмодзи: #{hex_color}")


@router.callback_query(F.data == "clear_recolor")
async def cb_clear_recolor(callback: CallbackQuery, state: FSMContext):
    await update_user_field(callback.from_user.id, "emoji_color", None)
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_text(
        format_main_menu_text(settings), reply_markup=get_main_menu_kb(settings), parse_mode="HTML"
    )
    await callback.answer("Цвет сброшен к оригиналу")


@router.message(SettingsStates.waiting_recolor)
async def msg_recolor(message: Message, state: FSMContext):
    hex_val = parse_color_input(message.text)
    if hex_val:
        await update_user_field(message.from_user.id, "emoji_color", hex_val)
        await state.clear()
        settings = await get_user_settings(message.from_user.id)
        await message.answer(
            f"{em(E.CHECK)} <b>Перекраска эмодзи установлена:</b> <code>#{hex_val}</code>\n\n" + format_main_menu_text(settings),
            reply_markup=get_main_menu_kb(settings),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"{em(E.CROSS)} Не удалось распознать цвет. Выбери кнопку из палитры, отправь HEX (например <code>FFFFFF</code>) или напиши название (<code>белый</code>, <code>серебро</code>, <code>золото</code>):",
            parse_mode="HTML",
        )
