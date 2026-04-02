# InstaAI — Vertical Video Generator

A minimal MVP web app that automatically generates short-form vertical videos
(Instagram Reels / TikTok) from user-uploaded images, video clips, audio, and captions.

**Output format:** 1080×1920 MP4 (H.264)

---

## Prerequisites

| Tool       | Version | Install                                     |
|------------|---------|---------------------------------------------|
| Python     | ≥ 3.10  | https://python.org                          |
| Node.js    | ≥ 18    | https://nodejs.org                          |
| FFmpeg     | ≥ 5.0   | https://ffmpeg.org/download.html            |

Make sure `python`, `node`, `npm`, and `ffmpeg` are on your system PATH.

---

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at **http://localhost:8000**.  
Docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at **http://localhost:5173**.  
The Vite dev server proxies `/generate-video` requests to the backend.

---

## Hebrew Font (Optional)

By default FFmpeg uses its built-in font. For better Hebrew rendering, set the
`FONT_PATH` environment variable to a Hebrew-compatible `.ttf` file:

```bash
# Windows PowerShell
$env:FONT_PATH="C:\Windows\Fonts\arial.ttf"

# Linux/macOS
export FONT_PATH="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
```

---

## Project Structure

```
InstaAI/
├── backend/
│   ├── main.py            # FastAPI app & /generate-video endpoint
│   ├── video_service.py   # High-level video composition pipeline
│   ├── ffmpeg_utils.py    # Low-level FFmpeg command builders
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       └── components/
│           ├── MediaUpload.jsx
│           ├── CaptionEditor.jsx
│           └── AudioUpload.jsx
└── README.md
```

---

## API

### `POST /generate-video`

| Field         | Type            | Description                                    |
|---------------|-----------------|------------------------------------------------|
| media_files   | File[]          | Image (jpg/png) or video (mp4) files           |
| durations     | string (JSON)   | Array of durations in seconds, e.g. `[3, 4]`   |
| captions      | string (JSON)   | Array of `{text, start, end, position}` objects |
| audio_file    | File (optional) | Background audio (mp3/wav)                      |
| audio_start   | float           | Audio trim start (seconds)                      |
| audio_end     | float           | Audio trim end (seconds)                        |

**Response:** The generated MP4 file (binary stream).

---

## Features

- Upload multiple images and video clips
- Per-item duration control
- Hebrew RTL captions with configurable position (top / center / bottom)
- Audio upload with start/end trimming
- Fade-in/out transitions between images
- Caption text with outline shadow for readability
- Dark, modern RTL interface
