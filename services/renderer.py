import asyncio
import os
import shutil
import tempfile
import uuid
from pathlib import Path

from config import (
    ASSETS_DIR,
    BACKGROUNDS_DIR,
    FONTS_DIR,
    MAX_DURATION_SECONDS,
    MAX_HEIGHT,
    MAX_RENDER_CONCURRENCY,
    MAX_WIDTH,
    MIN_HEIGHT,
    MIN_WIDTH,
    RENDER_TIMEOUT_SECONDS,
)

RENDER_SEMAPHORE = asyncio.Semaphore(MAX_RENDER_CONCURRENCY)


def get_media_duration_sync(file_path: Path) -> float:
    import subprocess
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path),
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception:
        pass
    return 3.0


_HAS_NVENC: bool | None = None


def has_nvenc() -> bool:
    global _HAS_NVENC
    if _HAS_NVENC is not None:
        return _HAS_NVENC
    import subprocess
    try:
        res = subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", "nullsrc=s=256x256:d=0.1",
                "-c:v", "h264_nvenc",
                "-f", "null", "-",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        _HAS_NVENC = (res.returncode == 0)
    except Exception:
        _HAS_NVENC = False
    return _HAS_NVENC


def to_safe_path(p: Path | str) -> str:
    path_str = str(p)
    if os.name == "nt":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(1000)
            res = ctypes.windll.kernel32.GetShortPathNameW(path_str, buf, 1000)
            if res > 0 and buf.value:
                return buf.value.replace("\\", "/")
        except Exception:
            pass
    return path_str.replace("\\", "/")


async def render_banner(
    user_settings: dict,
    input_source: Path,
    output_dir: Path,
    is_png_sequence: bool = False,
    sequence_fps: int = 60,
    sequence_duration: float = 3.0,
) -> Path:
    """
    Ультралегкий и бесшумный рендеринг 60 FPS Telegram-анимации на NVENC.
    """
    async with RENDER_SEMAPHORE:
        width = int(user_settings.get("width", 1920))
        height = int(user_settings.get("height", 530))
        width = max(MIN_WIDTH, min(MAX_WIDTH, width))
        height = max(MIN_HEIGHT, min(MAX_HEIGHT, height))

        if width % 2 != 0:
            width += 1
        if height % 2 != 0:
            height += 1

        bg_color = (user_settings.get("bg_color") or "000000").replace("#", "").upper()
        if len(bg_color) != 6:
            bg_color = "000000"

        bg_style = user_settings.get("bg_style", "solid")
        emoji_scale = max(20, min(300, int(user_settings.get("emoji_scale", 100))))
        emoji_color = user_settings.get("emoji_color")
        if emoji_color:
            emoji_color = emoji_color.replace("#", "").upper()
            if len(emoji_color) != 6:
                emoji_color = None

        shadow_3d = int(user_settings.get("shadow_3d", 1))
        watermark_text = user_settings.get("watermark_text")
        watermark_color = (user_settings.get("watermark_color") or "FFFFFF").replace("#", "")
        watermark_pos = user_settings.get("watermark_pos", "bottom_right")

        if is_png_sequence:
            loop_duration = max(1.0, min(MAX_DURATION_SECONDS, sequence_duration))
        else:
            ext = input_source.suffix.lower()
            if ext in (".webm", ".mp4"):
                loop_duration = await asyncio.to_thread(get_media_duration_sync, input_source)
                if loop_duration <= 0.1:
                    loop_duration = 3.0
                elif loop_duration > MAX_DURATION_SECONDS:
                    loop_duration = MAX_DURATION_SECONDS
            else:
                loop_duration = 3.0

        output_file = output_dir / f"banner_{uuid.uuid4().hex[:10]}.mp4"

        filter_complex_parts = []
        inputs = []

        # 1. Фон
        bg_video_path = None
        available_bgs = ("silk", "grid", "grain", "topo", "particles", "spotlight", "scanline", "rain")
        if bg_style in available_bgs:
            bg_video_path = BACKGROUNDS_DIR / f"{bg_style}.mp4"
        elif bg_style == "custom" and user_settings.get("custom_media_path"):
            p = Path(user_settings["custom_media_path"])
            if p.exists():
                bg_video_path = p

        if bg_video_path and bg_video_path.exists():
            inputs.extend(["-stream_loop", "-1", "-i", to_safe_path(bg_video_path)])
            filter_complex_parts.append(
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=60[bg];"
            )
        else:
            filter_complex_parts.append(
                f"color=c=0x{bg_color}:s={width}x{height}:r=60:d={loop_duration:.2f}[bg];"
            )

        # 2. Стикер / Эмодзи
        sticker_idx = inputs.count("-i")

        if is_png_sequence:
            pattern = f"{to_safe_path(input_source)}/f_%04d.png"
            inputs.extend(["-framerate", str(sequence_fps), "-i", pattern])
            stk_in = f"[{sticker_idx}:v]"
        else:
            ext = input_source.suffix.lower()
            if ext in (".webp", ".png", ".jpg"):
                inputs.extend(["-loop", "1", "-i", to_safe_path(input_source)])
            else:
                inputs.extend(["-i", to_safe_path(input_source)])
            stk_in = f"[{sticker_idx}:v]"

        max_allowed_w = int(width * 0.90 * (emoji_scale / 100.0))
        max_allowed_h = int(height * 0.75 * (emoji_scale / 100.0))
        if max_allowed_w % 2 != 0:
            max_allowed_w += 1
        if max_allowed_h % 2 != 0:
            max_allowed_h += 1

        scale_filter = f"scale='min({max_allowed_w},iw*min({max_allowed_w}/iw,{max_allowed_h}/ih))':'min({max_allowed_h},ih*min({max_allowed_w}/iw,{max_allowed_h}/ih))':force_original_aspect_ratio=decrease"
        stk_pipeline = f"{stk_in}fps=60,{scale_filter},format=rgba"

        # Легкая аппаратная перекраска через матрицу яркости (0% нагрузки на CPU)
        if emoji_color:
            r_norm = int(emoji_color[0:2], 16) / 255.0
            g_norm = int(emoji_color[2:4], 16) / 255.0
            b_norm = int(emoji_color[4:6], 16) / 255.0
            rr, rg, rb = r_norm * 0.299, r_norm * 0.587, r_norm * 0.114
            gr, gg, gb = g_norm * 0.299, g_norm * 0.587, g_norm * 0.114
            br, bg, bb = b_norm * 0.299, b_norm * 0.587, b_norm * 0.114
            stk_pipeline += f",colorchannelmixer=rr={rr:.3f}:rg={rg:.3f}:rb={rb:.3f}:gr={gr:.3f}:gg={gg:.3f}:gb={gb:.3f}:br={br:.3f}:bg={bg:.3f}:bb={bb:.3f}"

        filter_complex_parts.append(f"{stk_pipeline}[em];")

        # 3. 3D Тень (через быстрый SIMD lutrgb без попиксельного geq)
        shadow_offset_y = int(max_allowed_h * 0.42)
        if shadow_3d == 1:
            filter_complex_parts.append(
                f"[em]split=2[em_orig][em_sh];"
                f"[em_sh]format=rgba,lutrgb=r=0:g=0:b=0:a=val*0.4,scale=iw:ih*0.25,boxblur=8:1[shadow];"
                f"[bg][shadow]overlay=(W-w)/2:(H-h)/2+{shadow_offset_y}[bg_sh];"
                f"[bg_sh][em_orig]overlay=(W-w)/2:(H-h)/2[comp]"
            )
        else:
            filter_complex_parts.append(
                f"[bg][em]overlay=(W-w)/2:(H-h)/2[comp]"
            )

        current_out = "[comp]"

        # 4. Вотермарка
        if watermark_text and watermark_text.strip():
            clean_text = watermark_text.strip().replace("'", "").replace(":", "\\:").replace("\\", "\\\\")
            rel_font_path = "assets/fonts/Inter-Bold.ttf"
            if not Path(rel_font_path).exists():
                rel_font_path = str((FONTS_DIR / "Inter-Bold.ttf").resolve()).replace("\\", "/").replace(":", "\\:")

            font_size = max(14, min(48, int(height * 0.05)))
            if watermark_pos == "bottom_left":
                x_expr = "40"
                y_expr = "H-th-30"
            elif watermark_pos == "top_right":
                x_expr = "W-tw-40"
                y_expr = "30"
            elif watermark_pos == "center":
                x_expr = "(W-tw)/2"
                y_expr = "H-th-30"
            else:
                x_expr = "W-tw-40"
                y_expr = "H-th-30"

            filter_complex_parts.append(
                f";{current_out}drawtext=text='{clean_text}':fontfile='{rel_font_path}':"
                f"fontcolor=0x{watermark_color}:fontsize={font_size}:x={x_expr}:y={y_expr}[final]"
            )
            current_out = "[final]"

        full_filter = "".join(filter_complex_parts)

        if has_nvenc():
            encoder_args = [
                "-c:v", "h264_nvenc",
                "-preset", "p4",
                "-tune", "hq",
                "-cq", "19",
                "-b:v", "0",
            ]
            thread_args = [
                "-threads", "1",
                "-filter_threads", "1",
                "-filter_complex_threads", "1",
            ]
        else:
            encoder_args = [
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "22",
            ]
            thread_args = [
                "-threads", "0",
            ]

        cmd = [
            "ffmpeg", "-y",
            *thread_args,
            *inputs,
            "-filter_complex", full_filter,
            "-map", current_out,
            *encoder_args,
            "-pix_fmt", "yuv420p",
            "-r", "60",
            "-t", f"{loop_duration:.2f}",
            "-an",
            "-movflags", "+faststart",
            to_safe_path(output_file),
        ]

        kwargs = {}
        if os.name == "nt":
            import subprocess
            if hasattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS"):
                kwargs["creationflags"] = subprocess.BELOW_NORMAL_PRIORITY_CLASS

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=RENDER_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            process.kill()
            raise TimeoutError("Превышено время рендеринга (таймаут).")

        if process.returncode != 0:
            err_msg = stderr.decode(errors="ignore")[-800:]
            raise RuntimeError(f"FFmpeg render error: {err_msg}")

        return output_file
