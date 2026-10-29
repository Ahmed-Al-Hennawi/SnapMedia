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
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements.txt
printf '\nSnapMedia is starting. Open http://127.0.0.1:5000\n\n'
python app.py
