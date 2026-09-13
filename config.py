import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PROXY_URL = os.getenv("PROXY_URL", "")
WEBAPP_COLOR_PICKER_URL = os.getenv("WEBAPP_COLOR_PICKER_URL", "https://color-picker-webapp.vercel.app")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "gifthemy").lstrip("@")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/gifthemy")

ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"

# Ограничения безопасности (строго 1 для исключения OOM на 512 МБ Render)
MAX_RENDER_CONCURRENCY = 1
RENDER_TIMEOUT_SECONDS = 150
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


def _file_hash(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    try:
        import hashlib
        stat = path.stat()
        with open(path, "rb") as f:
            chunk = f.read(65536)
        return hashlib.md5(f"{stat.st_size}_{chunk}".encode("latin1", errors="ignore")).hexdigest()
    except Exception:
        return ""


def get_cached_file_id(key: str, file_path: Path | None = None) -> str | None:
    if CACHE_FILE.exists():
        try:
            import json
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            entry = data.get(key)
            if isinstance(entry, dict):
                expected_hash = _file_hash(file_path)
                if expected_hash and entry.get("hash") != expected_hash:
                    return None
                return entry.get("file_id")
            elif isinstance(entry, str):
                if file_path:
                    return None
                return entry
        except Exception:
            pass
    return None


def save_cached_file_id(key: str, file_id: str, file_path: Path | None = None) -> None:
    try:
        import json
        data = {}
        if CACHE_FILE.exists():
            try:
                data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        fhash = _file_hash(file_path)
        data[key] = {"file_id": file_id, "hash": fhash} if fhash else file_id
        CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass

