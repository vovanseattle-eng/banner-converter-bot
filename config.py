import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PROXY_URL = os.getenv("PROXY_URL", "")
WEBAPP_COLOR_PICKER_URL = os.getenv("WEBAPP_COLOR_PICKER_URL", "https://color-picker-webapp.vercel.app")

ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"

# Ограничения безопасности
MAX_RENDER_CONCURRENCY = 2
RENDER_TIMEOUT_SECONDS = 45
MAX_WIDTH = 2560
MAX_HEIGHT = 1440
MIN_WIDTH = 300
MIN_HEIGHT = 100
MAX_DURATION_SECONDS = 10.0

# 60 FPS Видео-баннеры
BANNER_MENU_PATH = ASSETS_DIR / "banner_1.mp4"
BANNER_SETTINGS_PATH = ASSETS_DIR / "banner_2.mp4"
BANNER_COLOR_PATH = ASSETS_DIR / "banner_3.mp4"
CACHE_FILE = ASSETS_DIR / "file_ids.json"


def get_cached_file_id(key: str) -> str | None:
    if CACHE_FILE.exists():
        try:
            import json
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            return data.get(key)
        except Exception:
            pass
    return None


def save_cached_file_id(key: str, file_id: str) -> None:
    try:
        import json
        data = {}
        if CACHE_FILE.exists():
            try:
                data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        data[key] = file_id
        CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass

