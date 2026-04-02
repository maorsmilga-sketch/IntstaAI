"""
Low-level FFmpeg command builders and runners.
All shell interactions with FFmpeg are isolated here.
"""

import subprocess
import shlex
import os
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
FONT_SIZE = 52
FONT_COLOR = "white"
BORDER_COLOR = "black"
BORDER_WIDTH = 3


def _run(cmd: List[str], description: str = "ffmpeg") -> None:
    """Run a subprocess command, log it, and raise on failure."""
    logger.info("%s command: %s", description, " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("%s stderr:\n%s", description, result.stderr)
        raise RuntimeError(f"{description} failed (exit {result.returncode}): {result.stderr[:500]}")


def probe_duration(file_path: str) -> float:
    """Return the duration of a media file in seconds."""
    cmd = [
        FFPROBE, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def image_to_segment(image_path: str, output_path: str, duration: float) -> None:
    """
    Convert a single image into a video segment at 1080x1920.
    Applies scale+pad to center the image without distortion and adds a fade-in/out.
    """
    fade_dur = min(0.4, duration / 3)
    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-framerate", str(FPS), "-t", str(duration),
        "-i", image_path,
        "-vf", (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"format=yuv420p,"
            f"fade=t=in:st=0:d={fade_dur},"
            f"fade=t=out:st={duration - fade_dur}:d={fade_dur}"
        ),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-t", str(duration),
        output_path,
    ]
    _run(cmd, "image_to_segment")


def normalize_video_segment(video_path: str, output_path: str, duration: Optional[float] = None) -> None:
    """
    Re-encode a user-uploaded video clip to match the project format (1080x1920, 30fps, no audio).
    If duration is provided the clip is trimmed.
    """
    dur_args = ["-t", str(duration)] if duration else []
    cmd = [
        FFMPEG, "-y",
        "-i", video_path,
        *dur_args,
        "-vf", (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"format=yuv420p"
        ),
        "-an",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        output_path,
    ]
    _run(cmd, "normalize_video_segment")


def concat_segments(segment_paths: List[str], output_path: str) -> None:
    """Concatenate a list of video segments using the concat demuxer."""
    list_file = output_path + ".txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in segment_paths:
            safe = p.replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe}'\n")

    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path,
    ]
    _run(cmd, "concat_segments")
    os.remove(list_file)


def trim_audio(audio_path: str, output_path: str, start: float, end: float) -> None:
    """Trim an audio file to [start, end) seconds."""
    cmd = [
        FFMPEG, "-y",
        "-i", audio_path,
        "-ss", str(start),
        "-to", str(end),
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]
    _run(cmd, "trim_audio")


def build_drawtext_filters(captions: list, font_path: Optional[str] = None) -> str:
    """
    Build a chain of FFmpeg drawtext filters from a list of caption dicts.
    Each caption: {text, start, end, position}
    RTL Hebrew is handled by setting text_shaping=1 (requires libfribidi in FFmpeg build).
    """
    filters = []
    for cap in captions:
        text = cap["text"].replace("'", "\u2019").replace(":", "\\:")
        start = float(cap["start"])
        end = float(cap["end"])
        position = cap.get("position", "bottom")

        if position == "top":
            y_expr = "h*0.08"
        elif position == "center":
            y_expr = "(h-text_h)/2"
        else:
            y_expr = "h*0.85-text_h"

        font_arg = f":fontfile='{font_path}'" if font_path else ""

        f = (
            f"drawtext=text='{text}'"
            f"{font_arg}"
            f":fontsize={FONT_SIZE}"
            f":fontcolor={FONT_COLOR}"
            f":borderw={BORDER_WIDTH}"
            f":bordercolor={BORDER_COLOR}"
            f":x=(w-text_w)/2"
            f":y={y_expr}"
            f":enable='between(t,{start},{end})'"
            f":text_shaping=1"
        )
        filters.append(f)

    return ",".join(filters) if filters else ""


def overlay_captions_and_audio(
    video_path: str,
    audio_path: Optional[str],
    captions: list,
    output_path: str,
    font_path: Optional[str] = None,
) -> None:
    """
    Final composition step: take the concatenated video, overlay caption text,
    and mux the trimmed audio track. Produces the final MP4.
    """
    drawtext = build_drawtext_filters(captions, font_path)

    inputs = ["-i", video_path]
    if audio_path:
        inputs += ["-i", audio_path]

    vf = drawtext if drawtext else "null"

    audio_map = []
    audio_opts = []
    if audio_path:
        audio_map = ["-map", "0:v:0", "-map", "1:a:0"]
        audio_opts = ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    else:
        audio_map = ["-map", "0:v:0"]

    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-vf", vf,
        *audio_map,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        *audio_opts,
        output_path,
    ]
    _run(cmd, "overlay_captions_and_audio")
