import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PROXY_URL = os.getenv("PROXY_URL", "http://127.0.0.1:10809")
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
