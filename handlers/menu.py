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
    user_id = message.from_user.id
    from services.subscription import check_user_subscription
    from database import is_terms_accepted
    is_sub = await check_user_subscription(message.bot, user_id)
    accepted = await is_terms_accepted(user_id)
    if not is_sub or not accepted:
        from legal_texts import UNIFIED_GATE_SCREEN
        from keyboards import get_unified_gate_kb
        await show_or_edit_banner(
            event=message,
            banner_path=config.BANNER_MENU_PATH,
            cache_key="menu_main",
            caption=UNIFIED_GATE_SCREEN,
            reply_markup=get_unified_gate_kb(config.CHANNEL_URL),
        )
        return

    settings = await get_user_settings(user_id)
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


@router.callback_query(F.data.in_({"action:accept_gate", "check_subscription"}))
async def cb_accept_gate(callback: CallbackQuery, state: FSMContext):
    from services.subscription import check_user_subscription, clear_user_subscription_cache
    from database import record_terms_acceptance

    user_id = callback.from_user.id
    clear_user_subscription_cache(user_id)

    is_sub = await check_user_subscription(callback.bot, user_id)
    if is_sub:
        await record_terms_acceptance(user_id)
        await callback.answer("Подписка подтверждена, доступ открыт!", show_alert=False)
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
            f"Для использования бота необходимо подписаться на наш канал @{config.CHANNEL_USERNAME}!",
            show_alert=True,
        )


@router.message(Command("terms"))
@router.callback_query(F.data == "legal:terms")
async def show_terms(event: Message | CallbackQuery):
    from legal_texts import TERMS_TEXT
    from keyboards import get_terms_doc_kb
    from helpers import safe_edit_caption_or_text
    if isinstance(event, CallbackQuery):
        await safe_edit_caption_or_text(event.message, text=TERMS_TEXT, reply_markup=get_terms_doc_kb())
        await event.answer()
    else:
        await event.answer(text=TERMS_TEXT, reply_markup=get_terms_doc_kb(), parse_mode="HTML")


@router.callback_query(F.data == "gate:back")
async def cb_gate_back(callback: CallbackQuery):
    from legal_texts import UNIFIED_GATE_SCREEN
    from keyboards import get_unified_gate_kb
    await show_or_edit_banner(
        event=callback,
        banner_path=config.BANNER_MENU_PATH,
        cache_key="menu_main",
        caption=UNIFIED_GATE_SCREEN,
        reply_markup=get_unified_gate_kb(config.CHANNEL_URL),
    )
    await callback.answer()



