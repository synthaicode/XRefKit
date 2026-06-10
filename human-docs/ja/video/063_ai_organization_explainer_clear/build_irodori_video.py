from __future__ import annotations

import csv
import os
import shlex
import shutil
import subprocess
import wave
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image


VIDEO_DIR = Path(__file__).resolve().parent
MANIFEST = VIDEO_DIR / "manifest_irodori.tsv"
AUDIO_DIR = VIDEO_DIR / "irodori_audio"
SEGMENT_DIR = VIDEO_DIR / "irodori_segments"
CONCAT_FILE = VIDEO_DIR / "irodori_concat.txt"
OUTPUT = VIDEO_DIR / "ai_team_explainer_clear_irodori.mp4"

IRODORI_REPO_DIR = os.environ.get("IRODORI_REPO_DIR", "").strip()
IRODORI_CHECKPOINT = os.environ.get(
    "IRODORI_CHECKPOINT",
    "Aratako/Irodori-TTS-500M-v2-VoiceDesign",
)
IRODORI_EXPLAINER_CAPTION = os.environ.get(
    "IRODORI_EXPLAINER_CAPTION",
    "落ち着いた解説者の声で、明瞭に自然な日本語で読み上げてください。",
)
IRODORI_LISTENER_CAPTION = os.environ.get(
    "IRODORI_LISTENER_CAPTION",
    "聞き手の声で、軽く自然な疑問を日本語で投げかけてください。",
)
IRODORI_EXTRA_ARGS = shlex.split(os.environ.get("IRODORI_EXTRA_ARGS", ""))

FPS = "24"
FPS_INT = 24
QUESTION_PAUSE_SECONDS = float(os.environ.get("IRODORI_QUESTION_PAUSE_SECONDS", "0.8"))
ANSWER_PAUSE_SECONDS = float(os.environ.get("IRODORI_ANSWER_PAUSE_SECONDS", "0.6"))
SLIDE_END_PAUSE_SECONDS = float(os.environ.get("IRODORI_SLIDE_END_PAUSE_SECONDS", "1.0"))
ANSWER_REVEAL_SECONDS = float(os.environ.get("IRODORI_ANSWER_REVEAL_SECONDS", "0.9"))
WAV_RATE = 48000
WAV_CHANNELS = 1
WAV_SAMPLE_WIDTH = 2
FRAME_SIZE = (1600, 900)


def ensure_irodori_repo() -> Path:
    if not IRODORI_REPO_DIR:
        raise RuntimeError(
            "IRODORI_REPO_DIR is required. Point it at a local clone of Aratako/Irodori-TTS."
        )
    repo_dir = Path(IRODORI_REPO_DIR).expanduser().resolve()
    infer_path = repo_dir / "infer.py"
    if not infer_path.is_file():
        raise RuntimeError(f"infer.py not found under IRODORI_REPO_DIR: {repo_dir}")
    return repo_dir


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def parse_turns(narration: str) -> list[tuple[str, str]]:
    turns: list[tuple[str, str]] = []
    for raw_turn in narration.split("｜"):
        turn = raw_turn.strip()
        if not turn:
            continue
        if ":" in turn:
            role, text = turn.split(":", 1)
        elif "：" in turn:
            role, text = turn.split("：", 1)
        else:
            role, text = "解説", turn
        turns.append((role.strip(), text.strip()))
    return turns


def caption_for_role(role: str) -> str:
    if role == "聞き手":
        return IRODORI_LISTENER_CAPTION
    return IRODORI_EXPLAINER_CAPTION


def synthesize(text: str, role: str, wav_path: Path) -> None:
    repo_dir = ensure_irodori_repo()
    command = [
        "uv",
        "run",
        "python",
        "infer.py",
        "--hf-checkpoint",
        IRODORI_CHECKPOINT,
        "--text",
        text,
        "--caption",
        caption_for_role(role),
        "--no-ref",
        "--output-wav",
        str(wav_path),
        *IRODORI_EXTRA_ARGS,
    ]
    subprocess.run(command, cwd=repo_dir, check=True)


def write_silence(path: Path, seconds: float) -> None:
    frame_count = max(1, round(WAV_RATE * seconds))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(WAV_CHANNELS)
        wav.setsampwidth(WAV_SAMPLE_WIDTH)
        wav.setframerate(WAV_RATE)
        wav.writeframes(b"\x00" * frame_count * WAV_CHANNELS * WAV_SAMPLE_WIDTH)


def run_ffmpeg(args: list[str]) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, "-y", *args], check=True)


def wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def load_frame(path: Path) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    if image.size != FRAME_SIZE:
        image = image.resize(FRAME_SIZE, Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.uint8)


def render_reveal_video(start_path: Path, end_path: Path, audio_path: Path, video_path: Path) -> None:
    start = load_frame(start_path).astype(np.float32)
    end = load_frame(end_path).astype(np.float32)
    duration = wav_duration_seconds(audio_path)
    frame_count = max(1, round(duration * FPS_INT))
    reveal_frames = max(1, round(min(ANSWER_REVEAL_SECONDS, duration) * FPS_INT))

    with imageio.get_writer(
        video_path,
        fps=FPS_INT,
        codec="libx264",
        quality=8,
        macro_block_size=1,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    ) as writer:
        for index in range(frame_count):
            if index < reveal_frames:
                t = index / max(1, reveal_frames - 1)
                alpha = t * t * (3 - 2 * t)
                frame = (start * (1 - alpha) + end * alpha).clip(0, 255).astype(np.uint8)
            else:
                frame = end.astype(np.uint8)
            writer.append_data(frame)


def concat_audio(audio_paths: list[Path], output_path: Path) -> None:
    concat_file = output_path.with_suffix(".txt")
    lines = [f"file '{path.as_posix()}'" for path in audio_paths]
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_ffmpeg(
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output_path),
        ]
    )


def build_dialogue_audio(order: str, narration: str) -> Path:
    turns = parse_turns(narration)
    turn_paths: list[Path] = []
    for index, (role, text) in enumerate(turns, start=1):
        wav_path = AUDIO_DIR / f"{order}_{index:02d}_{role}.wav"
        synthesize(text, role, wav_path)
        turn_paths.append(wav_path)

        pause_seconds = QUESTION_PAUSE_SECONDS if role == "聞き手" else ANSWER_PAUSE_SECONDS
        pause_path = AUDIO_DIR / f"{order}_{index:02d}_{role}_pause.wav"
        write_silence(pause_path, pause_seconds)
        turn_paths.append(pause_path)

    if not (len(turns) == 1 and turns[0][0] == "聞き手"):
        end_pause_path = AUDIO_DIR / f"{order}_end_pause.wav"
        write_silence(end_pause_path, SLIDE_END_PAUSE_SECONDS)
        turn_paths.append(end_pause_path)

    if len(turn_paths) == 1:
        return turn_paths[0]

    merged_path = AUDIO_DIR / f"{order}.wav"
    concat_audio(turn_paths, merged_path)
    return merged_path


def build_segment(slide_path: Path, audio_path: Path, segment_path: Path) -> None:
    run_ffmpeg(
        [
            "-loop",
            "1",
            "-framerate",
            FPS,
            "-i",
            str(slide_path),
            "-i",
            str(audio_path),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            "-movflags",
            "+faststart",
            str(segment_path),
        ]
    )


def build_reveal_segment(
    question_slide_path: Path,
    answer_slide_path: Path,
    audio_path: Path,
    segment_path: Path,
) -> None:
    temp_video_path = segment_path.with_name(f"{segment_path.stem}_reveal_video.mp4")
    render_reveal_video(question_slide_path, answer_slide_path, audio_path, temp_video_path)
    run_ffmpeg(
        [
            "-i",
            str(temp_video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(segment_path),
        ]
    )


def concat_segments(segment_paths: list[Path]) -> None:
    lines = [f"file '{path.as_posix()}'" for path in segment_paths]
    CONCAT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_ffmpeg(
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(CONCAT_FILE),
            "-r",
            FPS,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(OUTPUT),
        ]
    )


def main() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    SEGMENT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_manifest()
    segments: list[Path] = []
    previous_slide_path: Path | None = None
    previous_order = ""

    for row in rows:
        order = row["order"]
        slide_path = (VIDEO_DIR / row["slide_path"]).resolve()
        segment_path = SEGMENT_DIR / f"{order}.mp4"
        wav_path = build_dialogue_audio(order, row["narration"])
        is_answer_reveal = (
            order.endswith("b")
            and previous_slide_path is not None
            and previous_order == f"{order[:-1]}a"
        )
        if is_answer_reveal:
            build_reveal_segment(previous_slide_path, slide_path, wav_path, segment_path)
        else:
            build_segment(slide_path, wav_path, segment_path)
        segments.append(segment_path.resolve())
        previous_slide_path = slide_path
        previous_order = order

    concat_segments(segments)
    print(f"checkpoint={IRODORI_CHECKPOINT}")
    print(f"listener_caption={IRODORI_LISTENER_CAPTION}")
    print(f"explainer_caption={IRODORI_EXPLAINER_CAPTION}")
    print(OUTPUT)


if __name__ == "__main__":
    if shutil.which("uv") is None:
        raise RuntimeError("uv is required in PATH to run Irodori-TTS inference.")
    main()
