from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import get_user_settings
from keyboards import get_main_menu_kb
from helpers import format_main_menu_text
from emoji import E, em

router = Router()


@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    settings = await get_user_settings(message.from_user.id)
    text = format_main_menu_text(settings)
    await message.answer(text, reply_markup=get_main_menu_kb(settings), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    settings = await get_user_settings(message.from_user.id)
    text = (
        f"{em(E.INFO)} <b>Инструкция по созданию баннера:</b>\n\n"
        f"<blockquote>"
        f"1. <b>Отправьте эмодзи или стикер:</b> любой анимированный стикер (TGS/WEBM) или строку премиум-эмодзи.\n"
        f"2. <b>Настройте сцену:</b> выберите цвет фона, 3D тень, разрешение и масштаб.\n"
        f"3. <b>Получите результат:</b> бот за секунды сгенерирует плавный 60 FPS баннер (MP4 + GIF)."
        f"</blockquote>"
    )
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
