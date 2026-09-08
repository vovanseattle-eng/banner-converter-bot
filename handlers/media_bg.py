from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_user_settings, update_user_field
from keyboards import get_media_kb, get_main_menu_kb
from helpers import format_main_menu_text
from states import SettingsStates
from emoji import E, em, title

router = Router()


@router.callback_query(F.data == "menu:media")
async def cb_media_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    settings = await get_user_settings(callback.from_user.id)
    has_custom = settings.get("bg_style") == "custom" and bool(settings.get("custom_media_path"))
    status = "Загружено" if has_custom else "Не установлено"
    text = (
        f"{title(E.MEDIA, 'Своя медиа для фона')}\n\n"
        f"<blockquote>Статус: <code>{status}</code>\n"
        f"Загрузи видео (MP4/WEBM) или изображение для использования в качестве фона.</blockquote>"
    )
    await callback.message.edit_text(text, reply_markup=get_media_kb(has_custom), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "upload_media")
async def cb_upload_media(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_custom_media)
    await callback.message.edit_text(
        f"{title(E.SEND, 'Отправь видео или картинку')} для фона баннера:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.waiting_custom_media, F.video | F.animation | F.photo | F.document)
async def msg_custom_media(message: Message, state: FSMContext):
    bot = message.bot
    file_id = None
    ext = ".mp4"

    if message.video:
        file_id = message.video.file_id
        ext = ".mp4"
    elif message.animation:
        file_id = message.animation.file_id
        ext = ".mp4"
    elif message.photo:
        file_id = message.photo[-1].file_id
        ext = ".jpg"
    elif message.document:
        file_id = message.document.file_id
        ext = Path(message.document.file_name or "file.mp4").suffix or ".mp4"

    if not file_id:
        await message.answer(f"{em(E.CROSS)} Пожалуйста, отправь видео, GIF или изображение.")
        return

    user_bg_dir = Path("user_backgrounds")
    user_bg_dir.mkdir(exist_ok=True)
    target_path = user_bg_dir / f"bg_{message.from_user.id}{ext}"

    file_info = await bot.get_file(file_id)
    await bot.download_file(file_info.file_path, destination=target_path)

    await update_user_field(message.from_user.id, "custom_media_path", str(target_path.resolve()))
    await update_user_field(message.from_user.id, "bg_style", "custom")
    await state.clear()

    settings = await get_user_settings(message.from_user.id)
    await message.answer(
        f"{em(E.CHECK)} <b>Медиа успешно установлено в качестве фона!</b>\n\n" + format_main_menu_text(settings),
        reply_markup=get_main_menu_kb(settings),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "reset_media")
async def cb_reset_media(callback: CallbackQuery):
    await update_user_field(callback.from_user.id, "bg_style", "solid")
    await update_user_field(callback.from_user.id, "custom_media_path", None)
    settings = await get_user_settings(callback.from_user.id)
    await callback.message.edit_text(
        f"{em(E.CHECK)} <b>Пользовательский фон сброшен на сплошной цвет.</b>\n\n" + format_main_menu_text(settings),
        reply_markup=get_main_menu_kb(settings),
        parse_mode="HTML",
    )
    await callback.answer("Фон сброшен")
