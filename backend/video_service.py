"""
High-level orchestrator that turns user inputs into a finished video.
Coordinates temp files and calls ffmpeg_utils for each processing step.
"""

import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import List, Optional

from ffmpeg_utils import (
    image_to_segment,
    normalize_video_segment,
    concat_segments,
    trim_audio,
    overlay_captions_and_audio,
)

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("outputs")
TEMP_DIR = Path("temp")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


def _ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)


def generate_video(
    media_items: List[dict],
    captions: list,
    audio_path: Optional[str],
    audio_start: float,
    audio_end: float,
    font_path: Optional[str] = None,
) -> str:
    """
    Main pipeline:
      1. Convert each media item to a normalized video segment
      2. Concatenate all segments
      3. Trim audio
      4. Overlay captions + attach audio
      5. Return path to final MP4

    media_items: [{"path": str, "duration": float}, ...]
    captions:    [{"text": str, "start": float, "end": float, "position": str}, ...]
    """
    _ensure_dirs()
    job_id = uuid.uuid4().hex[:10]
    job_temp = TEMP_DIR / job_id
    job_temp.mkdir(exist_ok=True)

    try:
        segments: List[str] = []

        for idx, item in enumerate(media_items):
            src = item["path"]
            dur = float(item["duration"])
            ext = Path(src).suffix.lower()
            seg_out = str(job_temp / f"seg_{idx:03d}.mp4")

            if ext in IMAGE_EXTENSIONS:
                image_to_segment(src, seg_out, dur)
            elif ext in VIDEO_EXTENSIONS:
                normalize_video_segment(src, seg_out, dur)
            else:
                raise ValueError(f"Unsupported media type: {ext}")

            segments.append(seg_out)

        concat_path = str(job_temp / "concat.mp4")
        if len(segments) == 1:
            shutil.copy2(segments[0], concat_path)
        else:
            concat_segments(segments, concat_path)

        trimmed_audio = None
        if audio_path and audio_end > audio_start:
            trimmed_audio = str(job_temp / "audio_trimmed.aac")
            trim_audio(audio_path, trimmed_audio, audio_start, audio_end)

        final_name = f"reel_{job_id}.mp4"
        final_path = str(OUTPUT_DIR / final_name)
        overlay_captions_and_audio(
            concat_path, trimmed_audio, captions, final_path, font_path
        )

        return final_path

    finally:
        shutil.rmtree(job_temp, ignore_errors=True)
