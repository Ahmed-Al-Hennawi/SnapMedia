#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Please install Python 3.11 or newer: brew install python'
  exit 1
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo 'Please install FFmpeg first: brew install ffmpeg'
  exit 1
fi
if ! command -v ffprobe >/dev/null 2>&1 || ! ffmpeg -hide_banner -encoders 2>/dev/null | grep -q 'libx264'; then
  echo 'FFmpeg must include ffprobe and the libx264 encoder: brew install ffmpeg'
  exit 1
fi
if ! command -v node >/dev/null 2>&1; then
  echo 'Install Node.js 22 or newer for full YouTube support: brew install node'
fi
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements.txt
printf '\nSnapMedia is starting. Open http://127.0.0.1:%s\n\n' "${PORT:-5000}"
python app.py
