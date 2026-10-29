# SnapMedia

SnapMedia is a responsive website for saving eligible public TikTok, Instagram, YouTube and Facebook media as MP4 or MP3. Use it only for content you own or have permission to save. Availability depends on each source platform.

## Features

- Four platform themes and automatic link detection.
- Standard and HD download choices, with MP4 selected by default.
- MP4 output normalized to H.264 video and AAC audio, then checked for a decodable video frame. AV1 and HEVC sources are converted automatically.
- Twelve interface languages, including Italian and right-to-left Arabic.
- Contact section and a Buy Me a Coffee panel. The support link shows “coming soon” until the account URL is added.
- Temporary downloads that expire after about one hour.

The site uses a real Python download backend. There are no simulated downloads or advertising prompts.

## Run locally

Install Python 3.11 or newer, FFmpeg with `ffprobe` and `libx264`, and Node.js 22 or newer. Node is needed for full YouTube extraction support through yt-dlp's bundled EJS component. On macOS with Homebrew:

```bash
brew install python ffmpeg node
./start-mac.sh
```

Alternatively, set up the environment manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. If that port is occupied, set `PORT` to another number before starting the app. Restart the server after changing Python code; a running process does not load edits automatically.

Paste one public video link, select MP4 or MP3, choose **Get download options**, then choose **Download** or **Download HD**. The server prepares and verifies the file before the browser downloads it. Conversion of a long AV1 or HEVC video may take several minutes.

## Contact and support

The Contact section displays `ahmed.alhennawi9@gmail.com`. The support buttons link to your [Buy Me a Coffee page](https://buymeacoffee.com/ahmed_alhennawi); update `buyMeACoffeeUrl` in `web/config.js` if your account URL changes.

## Deploy

Install the dependencies above on a Linux host with enough CPU, storage and bandwidth for video conversion. Install Python packages from `requirements.txt`, then run the app behind HTTPS using a production WSGI server. For a single-instance deployment:

```bash
export SNAPMEDIA_SITE_URL="https://your-real-domain.example"
gunicorn --workers 1 --threads 8 --timeout 120 --bind "0.0.0.0:${PORT:-8000}" app:app
```

Set `SNAPMEDIA_SITE_URL` to the final public HTTPS origin, without a path. It is needed for canonical links, the sitemap and social previews. If your HTTPS proxy sets forwarding headers, set `SNAPMEDIA_TRUSTED_PROXY_COUNT` to the exact number of trusted proxy hops; its default is `0`.

Use **one worker process** with the current in-memory job store. All requests for a job must reach the same instance, and its temporary files must remain on local writable storage until downloaded. A process restart clears active jobs. Before scaling to multiple instances, move job state to a shared queue and use shared file storage.

The app limits expensive information and download requests per client. Add distributed rate limits and outbound network restrictions at the hosting layer before making the service public. Allowed platform hostnames in the app are not a complete defense against server-side request forgery through redirects or provider behavior. Review the Terms and Privacy pages for your hosting provider, region and business details before launch. The current site does not load advertising scripts.

See [launch readiness](docs/launch-readiness.md) for the full hosting, search engine, security and growth checklist, including Search Console and Bing setup. `/robots.txt` and `/sitemap.xml` are served by Flask using your configured public URL.

The `/api/health` endpoint reports whether FFmpeg, FFprobe, libx264 and Node are found and identifies the media pipeline. It does not guarantee that any third-party platform will provide a downloadable format.

## Verify

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pip_audit --local
```

The tests cover URL validation, page routes, SEO output, request limits and MP4 conversion. A current real-world platform link should also be tested after deployment, because source platforms change their formats and extraction rules.

[yt-dlp's format and EJS documentation](https://github.com/yt-dlp/yt-dlp/wiki/EJS) and [Flask's production server guidance](https://flask.palletsprojects.com/en/stable/deploying/) describe the external runtime and hosting requirements.
