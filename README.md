# SnapMedia

![SnapMedia website walkthrough](docs/assets/snapmedia-demo.gif)

SnapMedia helps you save public videos from **TikTok, Instagram, YouTube, and Facebook** as MP4 video or MP3 audio. Paste a link, choose a format and quality, and download the finished file. Use it only for content you own or have permission to save; availability depends on the source platform.

## What it offers

- **One place for four platforms:** SnapMedia recognizes the platform from the link and adjusts the interface automatically.
- **Video or audio:** Choose MP4 with sound or MP3 audio, with standard and HD options where the source supports them.
- **Playable MP4 files:** Video is normalized to H.264 with AAC audio and checked for a decodable frame before download.
- **A comfortable interface:** Responsive layout, a one-tap link clear button, and 12 languages, including Italian and right-to-left Arabic.
- **No account required:** Prepared files are temporary and expire after about one hour.

The site uses a Flask backend, yt-dlp, and FFmpeg to prepare real downloads. It does not include simulated download buttons or advertising prompts.

## Try it locally

You'll need **Python 3.11+**, **FFmpeg** with `ffprobe` and the `libx264` encoder, and **Node.js 22+** for full YouTube extraction support.

On macOS with Homebrew:

```bash
brew install python ffmpeg node
./start-mac.sh
```

Or install the requirements and start the app yourself:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. If port 5000 is in use, start with `PORT=5001 python app.py` and open the matching address.

To save a file, paste a public video link, choose **MP4** or **MP3**, select **Get download options**, then choose **Download** or **Download HD**. Long videos that need conversion can take several minutes.

## Deploy

Use a Linux host with enough CPU, disk space, and bandwidth for video conversion. Install the Python requirements, FFmpeg, FFprobe, `libx264`, and Node.js, then run Gunicorn behind an HTTPS reverse proxy:

```bash
export SNAPMEDIA_SITE_URL="https://your-domain.example"
gunicorn --workers 1 --threads 8 --timeout 120 --bind "0.0.0.0:${PORT:-8000}" app:app
```

Set `SNAPMEDIA_SITE_URL` to your final HTTPS origin, without a path. It supplies the site's canonical URLs, social previews, and sitemap. If a trusted proxy sets forwarding headers, set `SNAPMEDIA_TRUSTED_PROXY_COUNT` to the exact number of trusted proxy hops; otherwise leave its default of `0`.

**Keep one worker process** with the current in-memory job store. Jobs and their temporary files must stay on the same instance until download, and a restart clears active jobs. Review the [launch checklist](docs/launch-readiness.md) before publishing, especially the hosting, network, legal, and platform checks. The `/api/health` endpoint checks local media tools but cannot confirm that an external platform will provide a downloadable format.

## Verify changes

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pip_audit --local
```

The tests cover URL validation, page routes, SEO output, request limits, and MP4 conversion. After deployment, also try a current permitted link from each platform; their formats and access rules can change.

## Contact

Questions or feedback? Email [ahmed.alhennawi9@gmail.com](mailto:ahmed.alhennawi9@gmail.com). If SnapMedia helps you, you can [buy me a coffee](https://buymeacoffee.com/ahmed_alhennawi). Support is optional.
