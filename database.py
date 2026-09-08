import json
from pathlib import Path
import aiosqlite

DB_PATH = Path(__file__).parent / "data.db"

DEFAULT_SETTINGS = {
    "bg_color": "000000",
    "width": 1920,
    "height": 530,
    "emoji_scale": 100,
    "emoji_color": None,
    "bg_style": "solid",  # solid, silk, grid, custom
    "custom_media_file_id": None,
    "shadow_3d": 1,  # 1 = включена 3D тень левитации
    "watermark_text": None,
    "watermark_font": "Inter",
    "watermark_color": "FFFFFF",
    "watermark_pos": "bottom_right",  # bottom_right, bottom_left, top_right, center
    "export_format": "mp4",
}


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                bg_color TEXT NOT NULL DEFAULT '000000',
                width INTEGER NOT NULL DEFAULT 1920,
                height INTEGER NOT NULL DEFAULT 530,
                emoji_scale INTEGER NOT NULL DEFAULT 100,
                emoji_color TEXT,
                bg_style TEXT NOT NULL DEFAULT 'solid',
                custom_media_file_id TEXT,
                shadow_3d INTEGER NOT NULL DEFAULT 1,
                watermark_text TEXT,
                watermark_font TEXT NOT NULL DEFAULT 'Inter',
                watermark_color TEXT NOT NULL DEFAULT 'FFFFFF',
                watermark_pos TEXT NOT NULL DEFAULT 'bottom_right',
                export_format TEXT NOT NULL DEFAULT 'mp4'
            )
            """
        )
        await db.commit()


async def get_user_settings(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)

    await set_user_settings(user_id, DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS, user_id=user_id)


async def set_user_settings(user_id: int, settings: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO user_settings (
                user_id, bg_color, width, height, emoji_scale, emoji_color,
                bg_style, custom_media_file_id, shadow_3d, watermark_text,
                watermark_font, watermark_color, watermark_pos, export_format
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                bg_color=excluded.bg_color,
                width=excluded.width,
                height=excluded.height,
                emoji_scale=excluded.emoji_scale,
                emoji_color=excluded.emoji_color,
                bg_style=excluded.bg_style,
                custom_media_file_id=excluded.custom_media_file_id,
                shadow_3d=excluded.shadow_3d,
                watermark_text=excluded.watermark_text,
                watermark_font=excluded.watermark_font,
                watermark_color=excluded.watermark_color,
                watermark_pos=excluded.watermark_pos,
                export_format=excluded.export_format
            """,
            (
                user_id,
                settings.get("bg_color", "000000"),
                settings.get("width", 1920),
                settings.get("height", 530),
                settings.get("emoji_scale", 100),
                settings.get("emoji_color"),
                settings.get("bg_style", "solid"),
                settings.get("custom_media_file_id"),
                settings.get("shadow_3d", 1),
                settings.get("watermark_text"),
                settings.get("watermark_font", "Inter"),
                settings.get("watermark_color", "FFFFFF"),
                settings.get("watermark_pos", "bottom_right"),
                settings.get("export_format", "mp4"),
            ),
        )
        await db.commit()


async def update_user_field(user_id: int, field: str, value):
    settings = await get_user_settings(user_id)
    settings[field] = value
    await set_user_settings(user_id, settings)


