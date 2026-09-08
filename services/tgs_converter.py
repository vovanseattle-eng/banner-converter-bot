import asyncio
from pathlib import Path
from rlottie_python import LottieAnimation


def render_tgs_to_png_sequence_sync(tgs_path: Path, output_dir: Path, target_size: int = 512) -> tuple[int, int]:
    """
    Ультрабыстрый (0.3 сек) рендеринг кадров векторного TGS в прозрачные PNG.
    Возвращает (total_frames, fps).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    anim = LottieAnimation.from_tgs(str(tgs_path))
    total_frames = anim.lottie_animation_get_totalframe()
    orig_fps = int(anim.lottie_animation_get_framerate() or 60)
    if orig_fps <= 0:
        orig_fps = 60

    for i in range(total_frames):
        im = anim.render_pillow_frame(i, width=target_size, height=target_size)
        im.save(output_dir / f"f_{i:04d}.png")

    return total_frames, orig_fps
