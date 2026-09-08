from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import (
    get_user_settings,
    get_user_presets,
    save_preset,
    load_preset,
    delete_preset,
)
from keyboards import get_presets_kb, get_main_menu_kb
from helpers import format_main_menu_text
from states import SettingsStates
from emoji import E, em, title

router = Router()


@router.message(Command("presets"))
async def cmd_presets(message: Message, state: FSMContext):
    await state.clear()
    presets = await get_user_presets(message.from_user.id)
    text = (
        f"{title(E.FILE, 'Заметки (Пресеты)')}\n\n"
        f"<blockquote>Сохраняй готовые конфигурации, чтобы применять их в один клик.</blockquote>"
    )
    await message.answer(text, reply_markup=get_presets_kb(presets), parse_mode="HTML")


@router.callback_query(F.data == "menu:presets")
async def cb_presets_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    presets = await get_user_presets(callback.from_user.id)
    text = (
        f"{title(E.FILE, 'Заметки (Пресеты)')}\n\n"
        f"<blockquote>Сохраняй готовые конфигурации, чтобы применять их в один клик.</blockquote>"
    )
    await callback.message.edit_text(text, reply_markup=get_presets_kb(presets), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "new_preset")
async def cb_new_preset(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_preset_name)
    await callback.message.edit_text(
        f"{title(E.EDIT, 'Введи название для заметки')} (до 20 символов):\n"
        "Например: <i>Темный баннер</i> или <i>Пак 1:1</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.waiting_preset_name)
async def msg_preset_name(message: Message, state: FSMContext):
    name = message.text.strip()[:20]
    settings = await get_user_settings(message.from_user.id)
    await save_preset(message.from_user.id, name, settings)
    await state.clear()
    presets = await get_user_presets(message.from_user.id)
    await message.answer(
        f"{em(E.CHECK)} <b>Заметка {name} сохранена!</b>",
        reply_markup=get_presets_kb(presets),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("load_preset:"))
async def cb_load_preset(callback: CallbackQuery):
    p_id = int(callback.data.split(":")[1])
    loaded = await load_preset(callback.from_user.id, p_id)
    if loaded:
        settings = await get_user_settings(callback.from_user.id)
        await callback.message.edit_text(
            f"{em(E.CHECK)} <b>Заметка применена!</b>\n\n" + format_main_menu_text(settings),
            reply_markup=get_main_menu_kb(settings),
            parse_mode="HTML",
        )
        await callback.answer("Настройки загружены!")
    else:
        await callback.answer("Заметка не найдена.", show_alert=True)


@router.callback_query(F.data.startswith("del_preset:"))
async def cb_del_preset(callback: CallbackQuery):
    p_id = int(callback.data.split(":")[1])
    await delete_preset(callback.from_user.id, p_id)
    presets = await get_user_presets(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=get_presets_kb(presets))
    await callback.answer("Заметка удалена")
