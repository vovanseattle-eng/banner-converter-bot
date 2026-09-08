import asyncio
from pathlib import Path
from PIL import Image
from rlottie_python import LottieAnimation


def render_single_emoji_to_memory(input_path: Path, target_size: int = 512) -> tuple[list[Image.Image], int]:
    """Рендерит один эмодзи прямо в оперативную память (без записи на диск!)."""
    ext = input_path.suffix.lower()

    if ext == ".tgs":
        anim = LottieAnimation.from_tgs(str(input_path))
        total_frames = anim.lottie_animation_get_totalframe()
        fps = int(anim.lottie_animation_get_framerate() or 60)
        if fps <= 0:
            fps = 60
        # Быстрый рендер кадров в RAM
        frames = [anim.render_pillow_frame(i, width=target_size, height=target_size) for i in range(total_frames)]
        return frames, fps

    elif ext in (".webp", ".png", ".jpg"):
        im = Image.open(input_path).convert("RGBA")
        if im.size != (target_size, target_size):
            im = im.resize((target_size, target_size), Image.Resampling.LANCZOS)
        # Статический эмодзи: 30 кадров в памяти
        return [im] * 30, 60

    else:
        # Для редких видео-стикеров извлекаем кадры
        import subprocess, tempfile
        t_dir = Path(tempfile.mkdtemp(prefix="webm_dec_"))
        try:
            cmd = [
                "ffmpeg", "-y",
                "-threads", "2",
                "-i", str(input_path),
                "-vf", f"scale={target_size}:{target_size}",
                "-pix_fmt", "rgba",
                str(t_dir / "f_%04d.png")
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            frames = [Image.open(p).copy() for p in sorted(t_dir.glob("f_*.png"))]
            return frames or [Image.new("RGBA", (target_size, target_size), (0,0,0,0))], 60
        finally:
            import shutil
            shutil.rmtree(t_dir, ignore_errors=True)


def stitch_emojis_in_memory_to_disk_sync(emoji_paths: list[Path], output_frames_dir: Path) -> tuple[int, int]:
    """
    Молниеносная склейка нескольких эмодзи в единую горизонтальную цепочку.
    Все промежуточные операции происходят в оперативной памяти,
    на диск сохраняется только готовая итоговая последовательность для FFmpeg.
    """
    output_frames_dir.mkdir(parents=True, exist_ok=True)
    k = len(emoji_paths)
    if k == 0:
        return 0, 60

    all_emoji_frames = []
    fps_list = []

    for ep in emoji_paths:
        frames, fps = render_single_emoji_to_memory(ep, target_size=384)
        all_emoji_frames.append(frames)
        fps_list.append(fps)

    total_frames = max(len(flist) for flist in all_emoji_frames)
    final_fps = max(fps_list) if fps_list else 60

    w_one, h_one = all_emoji_frames[0][0].size
    total_width = w_one * k

    # Склеиваем полосу и пишем только итоговые кадры
    for frame_idx in range(total_frames):
        strip = Image.new("RGBA", (total_width, h_one), (0, 0, 0, 0))
        for col_idx, flist in enumerate(all_emoji_frames):
            piece = flist[frame_idx % len(flist)]
            strip.paste(piece, (col_idx * w_one, 0), piece)

        strip.save(output_frames_dir / f"f_{frame_idx:04d}.png", "PNG", compress_level=0)

    return total_frames, final_fps
