from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from database import get_user_settings
from keyboards import get_main_menu_kb
from helpers import format_main_menu_text

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    settings = await get_user_settings(message.from_user.id)
    text = format_main_menu_text(settings)
    await message.answer(text, reply_markup=get_main_menu_kb(settings), parse_mode="HTML")


@router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    text = format_main_menu_text(settings)
    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu_kb(settings), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=get_main_menu_kb(settings), parse_mode="HTML")
    await callback.answer()
