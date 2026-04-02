"""
FastAPI application — single endpoint that accepts media, captions, audio
and returns a generated 1080x1920 vertical video.
"""

import json
import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from video_service import generate_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="InstaAI Video Generator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

FONT_PATH = os.environ.get("FONT_PATH", None)


def _save_upload(upload: UploadFile, subdir: str = "") -> str:
    """Persist an uploaded file to disk and return its path."""
    dest_dir = UPLOAD_DIR / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex[:8]}_{upload.filename}"
    dest = dest_dir / safe_name
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return str(dest)


@app.post("/generate-video")
async def generate_video_endpoint(
    media_files: List[UploadFile] = File(..., description="Image or video files"),
    durations: str = Form(..., description='JSON array of durations in seconds, e.g. [3, 4, 2]'),
    captions: str = Form(default="[]", description='JSON array of caption objects'),
    audio_file: Optional[UploadFile] = File(default=None, description="Audio file (mp3/wav)"),
    audio_start: float = Form(default=0.0),
    audio_end: float = Form(default=0.0),
):
    """
    Generate a vertical short-form video.

    - **media_files**: images (jpg/png) or video clips (mp4)
    - **durations**: JSON array matching media_files, seconds per item
    - **captions**: JSON array of `{text, start, end, position}`
    - **audio_file**: optional background audio
    - **audio_start / audio_end**: trim bounds for audio (seconds)
    """
    try:
        dur_list = json.loads(durations)
    except json.JSONDecodeError:
        raise HTTPException(400, "durations must be a valid JSON array")

    if len(dur_list) != len(media_files):
        raise HTTPException(400, "durations length must match number of media files")

    try:
        caption_list = json.loads(captions)
    except json.JSONDecodeError:
        raise HTTPException(400, "captions must be valid JSON")

    job_id = uuid.uuid4().hex[:8]

    media_items = []
    for i, mf in enumerate(media_files):
        saved = _save_upload(mf, subdir=job_id)
        media_items.append({"path": saved, "duration": dur_list[i]})

    audio_path = None
    if audio_file and audio_file.filename:
        audio_path = _save_upload(audio_file, subdir=job_id)

    try:
        result_path = generate_video(
            media_items=media_items,
            captions=caption_list,
            audio_path=audio_path,
            audio_start=audio_start,
            audio_end=audio_end,
            font_path=FONT_PATH,
        )
    except Exception as e:
        logger.exception("Video generation failed")
        raise HTTPException(500, f"Video generation failed: {str(e)}")
    finally:
        upload_job_dir = UPLOAD_DIR / job_id
        if upload_job_dir.exists():
            shutil.rmtree(upload_job_dir, ignore_errors=True)

    return FileResponse(
        result_path,
        media_type="video/mp4",
        filename=Path(result_path).name,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
