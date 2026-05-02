from __future__ import annotations

import csv
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
VIDEO_DIR = ROOT / "ja" / "docs" / "video" / "065_xrefkit_repository_overview"
MANIFEST = VIDEO_DIR / "manifest.tsv"
OUTPUT = VIDEO_DIR / "xrefkit_repository_overview_ja.mp4"
FPS = 24
SIZE = (1600, 900)


def duration_seconds(narration: str) -> float:
    if narration.startswith("聞き手"):
        return max(3.0, min(7.0, len(narration) / 8.5 + 1.0))
    return max(7.0, min(22.0, len(narration) / 8.5 + 1.8))


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def load_frame(path: Path) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    if image.size != SIZE:
        image = image.resize(SIZE, Image.Resampling.LANCZOS)
    return np.asarray(image)


def main() -> None:
    rows = read_manifest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with imageio.get_writer(
        OUTPUT,
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=1,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    ) as writer:
        for row in rows:
            slide_path = (VIDEO_DIR / row["slide_path"]).resolve()
            frame = load_frame(slide_path)
            frame_count = round(duration_seconds(row["narration"]) * FPS)
            for _ in range(frame_count):
                writer.append_data(frame)

    print(OUTPUT)


if __name__ == "__main__":
    main()
