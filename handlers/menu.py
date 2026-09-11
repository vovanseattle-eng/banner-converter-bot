from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import get_user_settings
from keyboards import get_main_menu_kb
from helpers import format_main_menu_text, show_or_edit_banner
from emoji import E, em
import config

router = Router()


@router.message(CommandStart())
@router.message(Command("menu"))
@router.message(Command("settings"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    settings = await get_user_settings(message.from_user.id)
    text = format_main_menu_text(settings)
    await show_or_edit_banner(
        event=message,
        banner_path=config.BANNER_MENU_PATH,
        cache_key="menu_main",
        caption=text,
        reply_markup=get_main_menu_kb(settings),
    )


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
    await show_or_edit_banner(
        event=message,
        banner_path=config.BANNER_MENU_PATH,
        cache_key="menu_main",
        caption=text,
        reply_markup=get_main_menu_kb(settings),
    )


@router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    text = format_main_menu_text(settings)
    try:
        await show_or_edit_banner(
            event=callback,
            banner_path=config.BANNER_MENU_PATH,
            cache_key="menu_main",
            caption=text,
            reply_markup=get_main_menu_kb(settings),
        )
    finally:
        await callback.answer()


@router.callback_query(F.data == "check_subscription")
async def cb_check_subscription(callback: CallbackQuery, state: FSMContext):
    from services.subscription import check_user_subscription, clear_user_subscription_cache

    user_id = callback.from_user.id
    clear_user_subscription_cache(user_id)

    is_sub = await check_user_subscription(callback.bot, user_id)
    if is_sub:
        await callback.answer("Подписка подтверждена!", show_alert=False)
        await state.clear()
        settings = await get_user_settings(user_id)
        text = format_main_menu_text(settings)
        await show_or_edit_banner(
            event=callback,
            banner_path=config.BANNER_MENU_PATH,
            cache_key="menu_main",
            caption=text,
            reply_markup=get_main_menu_kb(settings),
        )
    else:
        await callback.answer(
            f"Вы пока не подписались на @{config.CHANNEL_USERNAME}! Пожалуйста, перейдите в канал и нажмите «Подписаться».",
            show_alert=True,
        )


