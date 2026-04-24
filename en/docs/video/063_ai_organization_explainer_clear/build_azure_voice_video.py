from __future__ import annotations

import csv
import html
import os
import subprocess
import urllib.request
import wave
from pathlib import Path

import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[4]
VIDEO_DIR = ROOT / "en" / "docs" / "video" / "063_ai_organization_explainer_clear"
MANIFEST = VIDEO_DIR / "manifest.tsv"
AUDIO_DIR = VIDEO_DIR / "azure_audio"
SEGMENT_DIR = VIDEO_DIR / "azure_segments"
CONCAT_FILE = VIDEO_DIR / "azure_concat.txt"
OUTPUT = VIDEO_DIR / "ai_team_explainer_clear_en_azure.mp4"

AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "")
QUESTION_VOICE = os.environ.get("AZURE_SPEECH_QUESTION_VOICE", "en-US-GuyNeural")
ANSWER_VOICE = os.environ.get("AZURE_SPEECH_ANSWER_VOICE", "en-US-JennyNeural")
FPS = "24"
QUESTION_PAUSE_SECONDS = float(os.environ.get("AZURE_SPEECH_QUESTION_PAUSE_SECONDS", "0.8"))
ANSWER_PAUSE_SECONDS = float(os.environ.get("AZURE_SPEECH_ANSWER_PAUSE_SECONDS", "0.6"))
SLIDE_END_PAUSE_SECONDS = float(os.environ.get("AZURE_SPEECH_SLIDE_END_PAUSE_SECONDS", "1.0"))
WAV_RATE = 24000
WAV_CHANNELS = 1
WAV_SAMPLE_WIDTH = 2


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def parse_role_and_text(narration: str) -> tuple[str, str]:
    if ":" not in narration:
        return "Answer", narration.strip()
    role, text = narration.split(":", 1)
    role = role.strip()
    if role not in {"Question", "Answer"}:
        role = "Answer"
    return role, text.strip()


def ssml(text: str, voice: str) -> bytes:
    escaped = html.escape(text, quote=True)
    payload = f"""<speak version="1.0" xml:lang="en-US">
  <voice xml:lang="en-US" name="{voice}">
    <prosody rate="+3%">{escaped}</prosody>
  </voice>
</speak>"""
    return payload.encode("utf-8")


def synthesize(text: str, role: str, wav_path: Path) -> None:
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        raise RuntimeError("AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must be set")

    voice = QUESTION_VOICE if role == "Question" else ANSWER_VOICE
    url = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    req = urllib.request.Request(
        url,
        data=ssml(text, voice),
        method="POST",
        headers={
            "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
            "User-Agent": "xrefkit-ai-team-video",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        wav_path.write_bytes(response.read())


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


def build_row_audio(order: str, narration: str) -> Path:
    role, text = parse_role_and_text(narration)
    speech_path = AUDIO_DIR / f"{order}_{role.lower()}.wav"
    synthesize(text, role, speech_path)

    pause_seconds = QUESTION_PAUSE_SECONDS if role == "Question" else ANSWER_PAUSE_SECONDS
    pause_path = AUDIO_DIR / f"{order}_{role.lower()}_pause.wav"
    write_silence(pause_path, pause_seconds)

    paths = [speech_path, pause_path]
    if role != "Question":
        end_pause_path = AUDIO_DIR / f"{order}_end_pause.wav"
        write_silence(end_pause_path, SLIDE_END_PAUSE_SECONDS)
        paths.append(end_pause_path)

    merged_path = AUDIO_DIR / f"{order}.wav"
    concat_audio(paths, merged_path)
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

    segments: list[Path] = []
    for row in read_manifest():
        order = row["order"]
        slide_path = (VIDEO_DIR / row["slide_path"]).resolve()
        segment_path = SEGMENT_DIR / f"{order}.mp4"
        audio_path = build_row_audio(order, row["narration"])
        build_segment(slide_path, audio_path, segment_path)
        segments.append(segment_path.resolve())

    concat_segments(segments)
    print(f"question_voice={QUESTION_VOICE}")
    print(f"answer_voice={ANSWER_VOICE}")
    print(OUTPUT)


if __name__ == "__main__":
    main()
