from __future__ import annotations

import csv
import json
import os
import subprocess
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
VIDEO_DIR = ROOT / "ja" / "docs" / "video" / "063_ai_organization_explainer_clear"
MANIFEST = VIDEO_DIR / "manifest.tsv"
AUDIO_DIR = VIDEO_DIR / "voicevox_audio"
SEGMENT_DIR = VIDEO_DIR / "voicevox_segments"
CONCAT_FILE = VIDEO_DIR / "voicevox_concat.txt"
OUTPUT = VIDEO_DIR / "ai_team_explainer_clear_voicevox.mp4"

VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://127.0.0.1:50021")
SPEAKER_NAME = os.environ.get("VOICEVOX_SPEAKER_NAME", "四国めたん")
STYLE_NAME = os.environ.get("VOICEVOX_STYLE_NAME", "ノーマル")
LISTENER_SPEAKER_NAME = os.environ.get("VOICEVOX_LISTENER_SPEAKER_NAME", "ずんだもん")
LISTENER_STYLE_NAME = os.environ.get("VOICEVOX_LISTENER_STYLE_NAME", "ノーマル")
FPS = "24"
FPS_INT = 24
QUESTION_PAUSE_SECONDS = float(os.environ.get("VOICEVOX_QUESTION_PAUSE_SECONDS", "0.8"))
ANSWER_PAUSE_SECONDS = float(os.environ.get("VOICEVOX_ANSWER_PAUSE_SECONDS", "0.6"))
SLIDE_END_PAUSE_SECONDS = float(os.environ.get("VOICEVOX_SLIDE_END_PAUSE_SECONDS", "1.0"))
ANSWER_REVEAL_SECONDS = float(os.environ.get("VOICEVOX_ANSWER_REVEAL_SECONDS", "0.9"))
WAV_RATE = 24000
WAV_CHANNELS = 1
WAV_SAMPLE_WIDTH = 2
FRAME_SIZE = (1600, 900)


def request_json(url: str, data: bytes | None = None) -> object:
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def request_bytes(url: str, payload: bytes, content_type: str = "application/json") -> bytes:
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": content_type},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def resolve_speaker_id(speaker_name: str, style_name: str) -> int:
    speakers = request_json(f"{VOICEVOX_URL}/speakers")
    for speaker in speakers:
        if speaker.get("name") != speaker_name:
            continue
        styles = speaker.get("styles", [])
        for style in styles:
            if style.get("name") == style_name:
                return int(style["id"])
        if styles:
            return int(styles[0]["id"])
    available = ", ".join(s.get("name", "") for s in speakers)
    raise RuntimeError(f"speaker not found: {speaker_name}. available: {available}")


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


def synthesize(text: str, speaker_id: int, wav_path: Path, query_path: Path) -> None:
    query = urllib.parse.urlencode({"text": text, "speaker": speaker_id})
    audio_query = request_json(f"{VOICEVOX_URL}/audio_query?{query}", data=b"")
    # Slightly speed up long narration so slide pacing stays compact.
    audio_query["speedScale"] = 1.05
    query_path.write_text(json.dumps(audio_query, ensure_ascii=False, indent=2), encoding="utf-8")
    payload = json.dumps(audio_query, ensure_ascii=False).encode("utf-8")
    wav = request_bytes(f"{VOICEVOX_URL}/synthesis?speaker={speaker_id}", payload)
    wav_path.write_bytes(wav)


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


def build_dialogue_audio(order: str, narration: str, speaker_ids: dict[str, int]) -> Path:
    turns = parse_turns(narration)
    turn_paths: list[Path] = []
    for index, (role, text) in enumerate(turns, start=1):
        speaker_id = speaker_ids.get(role, speaker_ids["解説"])
        wav_path = AUDIO_DIR / f"{order}_{index:02d}_{role}.wav"
        query_path = AUDIO_DIR / f"{order}_{index:02d}_{role}_query.json"
        synthesize(text, speaker_id, wav_path, query_path)
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
    speaker_ids = {
        "解説": resolve_speaker_id(SPEAKER_NAME, STYLE_NAME),
        "聞き手": resolve_speaker_id(LISTENER_SPEAKER_NAME, LISTENER_STYLE_NAME),
    }
    rows = read_manifest()
    segments: list[Path] = []
    previous_slide_path: Path | None = None
    previous_order = ""

    for row in rows:
        order = row["order"]
        slide_path = (VIDEO_DIR / row["slide_path"]).resolve()
        segment_path = SEGMENT_DIR / f"{order}.mp4"
        wav_path = build_dialogue_audio(order, row["narration"], speaker_ids)
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
    print(f"speaker=解説:{SPEAKER_NAME}/{STYLE_NAME} id={speaker_ids['解説']}")
    print(f"speaker=聞き手:{LISTENER_SPEAKER_NAME}/{LISTENER_STYLE_NAME} id={speaker_ids['聞き手']}")
    print(OUTPUT)


if __name__ == "__main__":
    main()
