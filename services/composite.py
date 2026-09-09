import asyncio
import gc
from pathlib import Path
from PIL import Image
from rlottie_python import LottieAnimation


class EmojiSource:
    """Легковесный источник кадров для одного эмодзи без перегрузки RAM."""

    def __init__(self, path: Path, target_size: int = 384):
        self.path = path
        self.target_size = target_size
        self.ext = path.suffix.lower()
        self.anim = None
        self.static_img = None
        self.temp_dir = None
        self.frame_paths = []
        self.total_frames = 1
        self.fps = 60
        self._init_source()

    def _init_source(self):
        if self.ext == ".tgs":
            self.anim = LottieAnimation.from_tgs(str(self.path))
            self.total_frames = max(1, self.anim.lottie_animation_get_totalframe())
            fps = int(self.anim.lottie_animation_get_framerate() or 60)
            self.fps = fps if fps > 0 else 60
        elif self.ext in (".webp", ".png", ".jpg"):
            im = Image.open(self.path).convert("RGBA")
            if im.size != (self.target_size, self.target_size):
                im = im.resize((self.target_size, self.target_size), Image.Resampling.LANCZOS)
            self.static_img = im
            self.total_frames = 1
            self.fps = 60
        else:
            import subprocess
            import tempfile
            self.temp_dir = Path(tempfile.mkdtemp(prefix="webm_src_"))
            cmd = [
                "ffmpeg", "-y",
                "-threads", "1",
                "-i", str(self.path),
                "-vf", f"scale={self.target_size}:{self.target_size}",
                "-pix_fmt", "rgba",
                str(self.temp_dir / "f_%04d.png"),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.frame_paths = sorted(self.temp_dir.glob("f_*.png"))
            self.total_frames = max(1, len(self.frame_paths))
            self.fps = 60

    def get_frame(self, idx: int) -> Image.Image:
        if self.anim:
            return self.anim.render_pillow_frame(
                idx % self.total_frames, width=self.target_size, height=self.target_size
            )
        elif self.static_img:
            return self.static_img
        elif self.frame_paths:
            p = self.frame_paths[idx % len(self.frame_paths)]
            return Image.open(p)
        return Image.new("RGBA", (self.target_size, self.target_size), (0, 0, 0, 0))

    def close(self):
        self.anim = None
        if self.static_img:
            try:
                self.static_img.close()
            except Exception:
                pass
            self.static_img = None
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)


def stitch_emojis_in_memory_to_disk_sync(emoji_paths: list[Path], output_frames_dir: Path) -> tuple[int, int]:
    """
    Потоковая склейка нескольких эмодзи в единую горизонтальную полосу.
    Кадры генерируются на лету (только текущий кадр в RAM), предотвращая OOM на Render Free.
    """
    output_frames_dir.mkdir(parents=True, exist_ok=True)
    k = len(emoji_paths)
    if k == 0:
        return 0, 60

    target_size = 384
    sources = [EmojiSource(ep, target_size=target_size) for ep in emoji_paths]

    try:
        total_frames = max(s.total_frames for s in sources)
        final_fps = max(s.fps for s in sources)

        # Ограничение длительности для защиты от переполнения диска (макс 6 сек)
        max_allowed_frames = final_fps * 6
        if total_frames > max_allowed_frames:
            total_frames = max_allowed_frames

        total_width = target_size * k

        for frame_idx in range(total_frames):
            strip = Image.new("RGBA", (total_width, target_size), (0, 0, 0, 0))
            for col_idx, src in enumerate(sources):
                piece = src.get_frame(frame_idx)
                strip.paste(piece, (col_idx * target_size, 0), piece)
                if piece is not src.static_img:
                    try:
                        piece.close()
                    except Exception:
                        pass

            strip.save(output_frames_dir / f"f_{frame_idx:04d}.png", "PNG", compress_level=0)
            try:
                strip.close()
            except Exception:
                pass

        return total_frames, final_fps
    finally:
        for s in sources:
            s.close()
        gc.collect()

