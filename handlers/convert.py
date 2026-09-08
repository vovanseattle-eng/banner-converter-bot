import asyncio
import tempfile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import (
    Message,
    FSInputFile,
    CallbackQuery,
)
from aiogram.enums import MessageEntityType

from database import get_user_settings
from services.renderer import render_banner
from services.tgs_converter import render_tgs_to_png_sequence_sync
from services.composite import stitch_emojis_in_memory_to_disk_sync
from keyboards import get_result_kb
from emoji import E, em

router = Router()

OUTPUTS_DIR = Path("renders")
OUTPUTS_DIR.mkdir(exist_ok=True)


async def process_media_render(message: Message, file_id: str, is_tgs: bool = False):
    bot = message.bot
    status_msg = await message.answer(f"{em(E.LOADING)} <b>Рендеринг 60 FPS баннера...</b>", parse_mode="HTML")
    settings = await get_user_settings(message.from_user.id)

    temp_dir = Path(tempfile.mkdtemp(prefix="render_dl_"))
    try:
        file_info = await bot.get_file(file_id)
        ext = Path(file_info.file_path).suffix.lower() or ".webm"
        input_path = temp_dir / f"input{ext}"
        await bot.download_file(file_info.file_path, destination=input_path)

        if ext == ".tgs" or is_tgs:
            frames_dir = temp_dir / "tgs_frames"
            total_frames, orig_fps = await asyncio.to_thread(
                render_tgs_to_png_sequence_sync, input_path, frames_dir, 384
            )
            duration = total_frames / max(1, orig_fps)
            result_path = await render_banner(
                settings,
                frames_dir,
                OUTPUTS_DIR,
                is_png_sequence=True,
                sequence_fps=orig_fps,
                sequence_duration=duration,
            )
        else:
            result_path = await render_banner(settings, input_path, OUTPUTS_DIR)

        caption = (
            f"{em(E.CHECK, '✅')} <b>Баннер готов!</b>\n\n"
            f"<blockquote>"
            f"↖ <b>Разрешение:</b> {settings.get('width', 1920)}×{settings.get('height', 530)} 60 FPS\n"
            f"⛶ <b>Формат:</b> GIF\n"
            f"❖ <b>Масштаб:</b> {settings.get('emoji_scale', 100)}%"
            f"</blockquote>"
        )

        await bot.send_animation(
            chat_id=message.chat.id,
            animation=FSInputFile(result_path),
            caption=caption,
            reply_markup=get_result_kb(result_path.name),
            parse_mode="HTML",
        )

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        err_text = str(e)
        if "TimeoutError" in err_text:
            err_text = "Таймаут обработки. Попробуй еще раз."
        await status_msg.edit_text(f"{em(E.CROSS)} Ошибка рендера: {err_text}", parse_mode="HTML")
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


async def process_multi_emoji_render(message: Message, stickers: list):
    """Сверхбыстрая обработка составных надписей (несколько эмодзи)."""
    bot = message.bot
    status_msg = await message.answer(
        f"{em(E.LOADING)} <b>Сборка составного баннера ({len(stickers)} элементов)...</b>", parse_mode="HTML"
    )
    settings = await get_user_settings(message.from_user.id)

    temp_dir = Path(tempfile.mkdtemp(prefix="multi_emoji_"))
    try:
        emoji_paths = []

        # Скачиваем файлы
        for idx, stk in enumerate(stickers):
            file_info = await bot.get_file(stk.file_id)
            ext = Path(file_info.file_path).suffix.lower() or ".webm"
            stk_path = temp_dir / f"emoji_{idx}{ext}"
            await bot.download_file(file_info.file_path, destination=stk_path)
            emoji_paths.append(stk_path)

        # Склеиваем кадры в RAM
        stitched_dir = temp_dir / "stitched_frames"
        total_frames, fps = await asyncio.to_thread(
            stitch_emojis_in_memory_to_disk_sync, emoji_paths, stitched_dir
        )
        duration = total_frames / max(1, fps)

        # Рендеринг финального баннера
        result_path = await render_banner(
            settings,
            stitched_dir,
            OUTPUTS_DIR,
            is_png_sequence=True,
            sequence_fps=fps,
            sequence_duration=duration,
        )

        caption = (
            f"{em(E.CHECK, '✅')} <b>Составной баннер готов!</b>\n\n"
            f"<blockquote>"
            f"↖ <b>Разрешение:</b> {settings.get('width', 1920)}×{settings.get('height', 530)} 60 FPS\n"
            f"⛶ <b>Формат:</b> GIF\n"
            f"✨ <b>Элементов:</b> {len(stickers)} · <b>Масштаб:</b> {settings.get('emoji_scale', 100)}%"
            f"</blockquote>"
        )

        await bot.send_animation(
            chat_id=message.chat.id,
            animation=FSInputFile(result_path),
            caption=caption,
            reply_markup=get_result_kb(result_path.name),
            parse_mode="HTML",
        )

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        err_text = str(e)
        if "TimeoutError" in err_text:
            err_text = "Таймаут обработки. Попробуй еще раз."
        await status_msg.edit_text(f"{em(E.CROSS)} Ошибка рендера: {err_text}", parse_mode="HTML")
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


# 1. Приём стикеров (WEBM, WEBP, TGS)
@router.message(F.sticker)
async def handle_sticker(message: Message):
    sticker = message.sticker
    await process_media_render(message, sticker.file_id, is_tgs=bool(sticker.is_animated))


# 2. Приём Telegram Premium эмодзи в тексте
@router.message(F.entities)
async def handle_custom_emoji(message: Message):
    custom_emojis = [
        e for e in (message.entities or []) if e.type == MessageEntityType.CUSTOM_EMOJI
    ]
    if not custom_emojis:
        return

    emoji_ids = [e.custom_emoji_id for e in custom_emojis]

    try:
        stickers = await message.bot.get_custom_emoji_stickers(custom_emoji_ids=emoji_ids)
        if not stickers:
            await message.answer(f"{em(E.CROSS)} Не удалось получить файлы премиум эмодзи от Telegram.")
            return

        if len(stickers) == 1:
            await process_media_render(message, stickers[0].file_id, is_tgs=bool(stickers[0].is_animated))
        else:
            await process_multi_emoji_render(message, stickers)

    except Exception as e:
        await message.answer(f"{em(E.CROSS)} Ошибка при загрузке премиум эмодзи: {e}")


# 3. Отправка документа без сжатия по кнопке
@router.callback_query(F.data.startswith("send_doc:"))
async def cb_send_doc(callback: CallbackQuery):
    filename = callback.data.split(":")[1]
    file_path = OUTPUTS_DIR / filename
    if file_path.exists():
        await callback.bot.send_document(
            chat_id=callback.message.chat.id,
            document=FSInputFile(file_path),
            caption=f"{em(E.FILE)} Исходный видеофайл без сжатия (60 FPS, H.264)",
            parse_mode="HTML",
        )
        await callback.answer("Файл отправлен")
    else:
        await callback.answer("Файл устарел или был удален.", show_alert=True)
