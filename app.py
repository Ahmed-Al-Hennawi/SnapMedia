"""SnapMedia — lightweight Flask + yt-dlp prototype.

Download only public media you own or are permitted to save. No logins,
private content access, credential handling, or DRM circumvention.
"""
from __future__ import annotations

import os
import json
import re
import shutil
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from flask import Flask, abort, jsonify, request, send_file, send_from_directory
from yt_dlp import YoutubeDL

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DOWNLOAD_DIR = ROOT / "instance" / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_URL_CHARS = 2000
MAX_DURATION_SECONDS = int(os.getenv("SNAPMEDIA_MAX_DURATION", "1800"))
MAX_FILE_BYTES = int(os.getenv("SNAPMEDIA_MAX_MB", "300")) * 1024 * 1024
FILE_TTL_SECONDS = 3600
MAX_ACTIVE_JOBS = 3

HOSTS = {
    "tiktok": ("tiktok.com", "tiktokv.com"),
    "youtube": ("youtube.com", "youtu.be"),
    "instagram": ("instagram.com", "instagr.am"),
    "facebook": ("facebook.com", "fb.watch", "fb.com", "facebook.watch"),
}

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # Only short JSON inputs
app.json.ensure_ascii = False
executor = ThreadPoolExecutor(max_workers=MAX_ACTIVE_JOBS, thread_name_prefix="snapmedia")
_jobs: dict[str, dict] = {}
_jobs_lock = threading.RLock()


class InputError(ValueError):
    pass


def identify_url(raw: str) -> tuple[str, str]:
    """Allow only direct HTTPS media links from strictly matched domains."""
    if not isinstance(raw, str) or not raw.strip() or len(raw) > MAX_URL_CHARS:
        raise InputError("Paste a valid video link (maximum 2,000 characters).")
    raw = raw.strip()
    try:
        parts = urlsplit(raw)
        hostname = (parts.hostname or "").lower().rstrip(".")
        if parts.scheme.lower() != "https" or not hostname or parts.username or parts.password or parts.port:
            raise InputError("Only secure public platform links (HTTPS) are supported.")
        if "\\" in raw or any(ord(c) < 32 for c in raw):
            raise InputError("Invalid URL characters.")
    except InputError:
        raise
    except ValueError as exc:
        raise InputError("Invalid video link.") from exc

    platform = next((platform for platform, domains in HOSTS.items()
                     if any(hostname == domain or hostname.endswith("." + domain)
                            for domain in domains)), None)
    if not platform:
        raise InputError("Use a public TikTok, YouTube, Instagram or Facebook link.")
    # Disallow unexpected ports, embedded credentials, javascript:, host lookalikes.
    if not parts.path or parts.path == "/":
        raise InputError("Paste a link to a video, not the platform home page.")
    # Fragments are not needed and should not be sent to the extractor.
    safe_url = urlunsplit(("https", parts.netloc, parts.path, parts.query, ""))
    return platform, safe_url


def ydl_base() -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ignoreerrors": False,
        "socket_timeout": 15,
        "retries": 1,
        "fragment_retries": 1,
        "extractor_retries": 1,
        "skip_download": True,
        "nocheckcertificate": False,
    }


def extract_metadata(url: str) -> dict:
    platform, safe_url = identify_url(url)
    with YoutubeDL(ydl_base()) as ydl:
        info = ydl.extract_info(safe_url, download=False)
    if not isinstance(info, dict) or info.get("_type") in ("playlist", "multi_video") or info.get("entries") is not None:
        raise InputError("Please share one public video or Reel, not a playlist.")
    duration = info.get("duration")
    if duration and float(duration) > MAX_DURATION_SECONDS:
        raise InputError("This video exceeds the 30-minute limit for this version.")
    if info.get("is_live") or info.get("live_status") in ("is_live", "is_upcoming"):
        raise InputError("Live videos are not supported.")
    filesize = info.get("filesize") or info.get("filesize_approx")
    if isinstance(filesize, (int, float)) and filesize > MAX_FILE_BYTES:
        raise InputError("This media file exceeds the server size limit.")
    thumb = info.get("thumbnail") or ""
    if not isinstance(thumb, str) or not thumb.startswith("https://"):
        thumb = ""
    return {
        "platform": platform,
        "url": safe_url,
        "title": str(info.get("title") or "Untitled video")[:180],
        "uploader": str(info.get("uploader") or info.get("channel") or "")[:90],
        "duration": int(duration) if isinstance(duration, (int, float)) else None,
        "thumbnail": thumb,
    }


def nice_filename(title: str, extension: str) -> str:
    # Keep Unicode titles and remove path/control characters.
    title = re.sub(r'[\\/:*?"<>|\x00-\x1f\x7f]+', "", title or "SnapMedia")
    title = re.sub(r"\s+", " ", title).strip(" .")[:90] or "SnapMedia"
    return f"SnapMedia - {title}.{extension}"


def clear_expired():
    now = time.time()
    with _jobs_lock:
        expired = [key for key, job in _jobs.items() if now - job["created"] > FILE_TTL_SECONDS
                   and job["status"] not in ("queued", "working")]
        for key in expired:
            _jobs.pop(key, None)
    for key in expired:
        shutil.rmtree(DOWNLOAD_DIR / key, ignore_errors=True)


def periodic_cleanup():
    """Delete expired files even when no new visitors arrive."""
    while True:
        try:
            clear_expired()
        except Exception:
            app.logger.exception("Failed to clean old downloads")
        time.sleep(300)


threading.Thread(target=periodic_cleanup, daemon=True, name="snapmedia-cleanup").start()


def set_job(job_id: str, **changes):
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(changes)


def media_streams(path: Path) -> list[dict]:
    """Read the actual codecs; an .mp4 extension alone says nothing about playback."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,pix_fmt", "-of", "json", str(path)],
        capture_output=True, text=True, check=True, timeout=30,
    )
    return json.loads(probe.stdout).get("streams", [])


def compatible_mp4(source: Path) -> Path:
    """Return an MP4 with widely playable H.264 video and AAC audio."""
    streams = media_streams(source)
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not video:
        raise RuntimeError("The downloaded file has no video stream.")

    output = source.parent / "media-compatible.mp4"
    copy_video = video.get("codec_name") == "h264" and video.get("pix_fmt") == "yuv420p"
    copy_audio = not audio or audio.get("codec_name") == "aac"
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
               "-i", str(source), "-map", "0:v:0", "-map", "0:a:0?"]
    command += ["-c:v", "copy"] if copy_video else [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p"]
    command += ["-c:a", "copy"] if copy_audio else ["-c:a", "aac", "-b:a", "160k"]
    command += ["-movflags", "+faststart", str(output)]
    subprocess.run(command, capture_output=True, check=True, timeout=3600)
    checked = media_streams(output)
    if not any(s.get("codec_type") == "video" and s.get("codec_name") == "h264"
               and s.get("pix_fmt") == "yuv420p" for s in checked):
        raise RuntimeError("The converted video is not H.264 MP4.")
    if audio and not any(s.get("codec_type") == "audio" and s.get("codec_name") == "aac"
                         for s in checked):
        raise RuntimeError("The converted audio is not AAC.")
    return output


def do_download(job_id: str, meta: dict, file_type: str, quality: str):
    dest = DOWNLOAD_DIR / job_id
    try:
        dest.mkdir(parents=True, exist_ok=True)
        set_job(job_id, status="working", progress=2)

        def progress_hook(data):
            if data.get("status") == "downloading":
                downloaded = data.get("downloaded_bytes") or 0
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                if total:
                    set_job(job_id, progress=min(94, max(3, int(downloaded / total * 90))))
                if downloaded > MAX_FILE_BYTES:
                    raise InputError("The file exceeded the server size limit.")
            elif data.get("status") == "finished":
                set_job(job_id, progress=95)

        options = ydl_base()
        options.update({
            "skip_download": False,
            "outtmpl": str(dest / "media.%(ext)s"),
            "progress_hooks": [progress_hook],
            "max_filesize": MAX_FILE_BYTES,
            "overwrites": True,
        })
        if file_type == "mp3":
            options.update({
                "format": "bestaudio/best",
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                                    "preferredquality": "192" if quality == "hd" else "128"}],
            })
        else:
            if quality == "hd":
                selection = "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4][height<=1080]/bv*[height<=1080]+ba/b[height<=1080]/b"
            else:
                selection = "b[ext=mp4][height<=720]/bv*[ext=mp4][height<=720]+ba[ext=m4a]/b[height<=720]/bv*[height<=720]+ba/b"
            options.update({
                "format": selection,
                "merge_output_format": "mp4",
            })
        with YoutubeDL(options) as ydl:
            ydl.extract_info(meta["url"], download=True)

        extension = file_type
        allowed = {".mp3"} if file_type == "mp3" else {".mp4", ".mkv", ".webm", ".mov"}
        candidates = [p for p in dest.iterdir() if p.is_file() and p.suffix.lower() in allowed]
        if not candidates:
            raise RuntimeError("Conversion did not produce the requested file. Check FFmpeg installation.")
        file_path = max(candidates, key=lambda p: p.stat().st_mtime)
        if file_type == "mp4":
            set_job(job_id, progress=96)
            file_path = compatible_mp4(file_path)
            for old_file in candidates:
                if old_file != file_path:
                    old_file.unlink(missing_ok=True)
        if file_path.stat().st_size > MAX_FILE_BYTES:
            raise InputError("The converted file exceeded the server size limit.")
        set_job(job_id, status="ready", progress=100, file=str(file_path),
                filename=nice_filename(meta["title"], extension))
    except Exception as exc:
        error = str(exc)
        # Do not reflect secret URLs or arbitrary extractor output to visitors.
        if not isinstance(exc, InputError):
            error = "This public video couldn't be downloaded. The platform may be restricting access or the format may be unavailable."
        set_job(job_id, status="error", error=error[:240], progress=0)
        shutil.rmtree(dest, ignore_errors=True)


@app.before_request
def maintenance():
    clear_expired()


@app.after_request
def secure_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="Request too large."), 413


@app.route("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.route("/terms")
def terms():
    return send_from_directory(WEB, "terms.html")


@app.route("/privacy")
def privacy():
    return send_from_directory(WEB, "privacy.html")


@app.route("/<path:filename>")
def static_files(filename):
    if "/" in filename or filename.startswith("."):
        abort(404)
    return send_from_directory(WEB, filename)


@app.get("/api/health")
def health():
    return jsonify(ok=True, ffmpeg=bool(shutil.which("ffmpeg")), platform_count=4, demo_ads=True)


@app.post("/api/info")
def info_route():
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify(error="Send a JSON object with a video URL."), 400
    try:
        platform, url = identify_url(body.get("url", ""))
        meta = extract_metadata(url)
        return jsonify(meta)
    except InputError as exc:
        return jsonify(error=str(exc)), 422
    except Exception:
        return jsonify(error="We couldn't read this video. Check that the link is public and try again."), 422


@app.post("/api/download")
def start_download():
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify(error="Send a JSON object with a video URL."), 400
    try:
        platform, url = identify_url(body.get("url", ""))
        file_type = body.get("format", "mp4")
        quality = body.get("quality", "standard")
        if file_type not in ("mp4", "mp3") or quality not in ("standard", "hd"):
            raise InputError("Choose MP4 or MP3 and a supported quality.")
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            return jsonify(error="FFmpeg and FFprobe are required on the server. Install them first."), 503
        # A fresh extraction here prevents trusting client-side metadata.
        meta = extract_metadata(url)
    except InputError as exc:
        return jsonify(error=str(exc)), 422
    except Exception:
        return jsonify(error="This video is unavailable. Check the public link."), 422

    with _jobs_lock:
        active = sum(job["status"] in ("queued", "working") for job in _jobs.values())
        if active >= MAX_ACTIVE_JOBS:
            return jsonify(error="SnapMedia is busy. Please try again shortly."), 429
        job_id = uuid.uuid4().hex
        _jobs[job_id] = {"created": time.time(), "status": "queued", "progress": 0,
                         "platform": platform, "title": meta["title"]}
    executor.submit(do_download, job_id, meta, file_type, quality)
    return jsonify(id=job_id, status="queued"), 202


@app.get("/api/jobs/<job_id>")
def job_status(job_id):
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        abort(404)
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            abort(404)
        result = {k: v for k, v in job.items() if k in ("status", "progress", "error", "filename", "title")}
    if result["status"] == "ready":
        result["download_url"] = f"/api/files/{job_id}"
    return jsonify(result)


@app.get("/api/files/<job_id>")
def fetch_file(job_id):
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        abort(404)
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job or job["status"] != "ready":
            abort(404)
        file_path, name = job["file"], job["filename"]
    if not Path(file_path).is_file():
        abort(404)
    ext = Path(file_path).suffix.lower()
    return send_file(file_path, as_attachment=True, download_name=name,
                     mimetype="audio/mpeg" if ext == ".mp3" else "video/mp4", max_age=0)


if __name__ == "__main__":
    # Development only. Use Gunicorn or another production WSGI server behind HTTPS.
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
