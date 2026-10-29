# SnapMedia — multi-platform media downloader (MVP)

An original, responsive website built with **HTML, CSS, vanilla JavaScript and Python (Flask)**. The website supports link inspection and MP4/MP3 downloading through `yt-dlp` with `FFmpeg`, to the extent a source makes public content available. You may download only media you own or are permitted to save. Some platforms prohibit downloads under their terms, even for public media.

## What is included

- TikTok dark, Instagram gradient-accented, YouTube red and Facebook blue themes, auto-detected from links.
- Mobile-first design; MP4 selected by default; MP3 as an alternative; Download (up to 720p/128 kbps) and Download HD (up to 1080p/192 kbps).
- Public-video metadata preview, server-side conversion, progress indicator, temporary downloadable files.
- 11 interface languages: English, Arabic (with right-to-left layout), Spanish, French, German, Portuguese, Indonesian, Turkish, Hindi, Japanese and Korean.
- Sections for How It Works, Features, About, frequently asked questions, Terms and Privacy. Legal document bodies are in English and Arabic only, with a visible English fallback for other languages.
- Ad banner placeholder and opt-in rewarded-ad flow: **demo mode by default**. No real revenue is generated in demo mode.
- No accounts or downloads-per-user quota. Technical limits prevent misuse: 30 minutes per source, 300 MB per file, 3 concurrent jobs, temporary file expiration of ~1 hour.

## Instant design preview (no setup)

Open `SnapMedia-Interactive-Demo.html` from the downloaded project. It is a standalone, offline, clickable preview of themes, languages, formats, video preview and the ad modal. Its link lookups and downloads are **simulated** and labelled clearly. For actual authorized public media downloads, run the full Python project below.

## Run locally on Mac

### 1. Install Python 3.11+ and FFmpeg

In Terminal:

```bash
brew install python ffmpeg
```

If Homebrew is not installed, visit https://brew.sh/ first. On some computers, Python is already installed (`python3 --version`).

### 2. Start SnapMedia

```bash
cd SnapMedia
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser. HTML files alone will not download videos: the Python backend must be running.

**Note:** `yt-dlp` currently recommends a supported JavaScript runtime for some YouTube content. `yt-dlp[default]` includes its matching EJS component; installing Node.js (`brew install node`) may improve compatibility. Some sites require further support as platforms change; none is guaranteed.

### 3. Try the flow

1. Select a platform, or paste a link and let SnapMedia detect it.
2. Keep MP4 or choose MP3.
3. Select **Get download options**.
4. Select **Download** or **Download HD**.
5. In demo mode click **Continue to download (demo)**. The server prepares the file, and your browser downloads it when ready.

Try only a public video you personally own or have explicit authorization to download.

## Advertising: how to make real revenue

`web/config.js` contains optional settings for a Google Ad Manager implementation. The included `web/ads.js` handles a rewarded slot through Google Publisher Tag (GPT): `rewardedSlotReady`, `rewardedSlotGranted`, and `rewardedSlotClosed`. It waits for the user to opt in, does not count abandoned ads as rewarded, and gracefully continues without an ad if no ad fills. There is an optional display banner slot too.

**To connect paid ads:**

1. Obtain approval from an ad network that accepts your website category, content and regional traffic. Do not assume a downloader site qualifies.
2. Check the ad provider's rewarded-ad rules (including voluntary opt-in and precise reward disclosure). Add the provider's **ad unit paths** to `web/config.js` and change `enabled` to `true` only after approval.
3. Add a legally appropriate cookie-consent / Consent Management Platform (CMP) before enabling ad-personalization features in applicable territories. Update Privacy Policy for the services actually in use.
4. **Important production warning:** the frontend ad callback is not secure proof that a user watched an ad. The included `/api/download` endpoint can be called directly, bypassing the visible ad prompt. **Before enforcing a real ad gate or paying for infrastructure**, implement a provider-supported server-verifiable reward or approved event receipt and one-time signed download entitlement. If the provider does not support this, treat ads as an optional funding mechanism, not an enforceable payment gate.
5. Do not click your own ads or simulate rewarded completions. The default placeholders and demo button are not paid ads.

References: [Google rewarded ad policies](https://support.google.com/admanager/answer/7496282), [Google Publisher Tag example](https://developers.google.com/publisher-tag/samples/display-rewarded-ad).

## Project structure

```
SnapMedia/
├── app.py               # URL validation, video metadata, download jobs, temporary file API
├── start-mac.sh         # One-command Mac setup and launcher
├── SnapMedia-Interactive-Demo.html # Self-contained clickable design preview
├── requirements.txt     # Flask + yt-dlp
├── web/
│   ├── index.html       # Home page and downloader
│   ├── styles.css       # Responsive layout and four themes
│   ├── i18n.js          # 11 UI languages
│   ├── app.js           # Interactive UI / download flow
│   ├── ads.js           # Optional rewarded + banner ad integration
│   ├── config.js        # Public configuration, demo ads by default
│   ├── terms.html       # Terms page
│   ├── privacy.html     # Privacy page
│   ├── legal.js         # Legal page content (English + Arabic)
│   └── favicon.svg
├── tests/
│   └── test_app.py
└── instance/downloads/ # Temporary output (not committed)
```

## Production checklist (important)

The delivered build is a **working software prototype**, not a production-ready revenue business. Before releasing to the public:

- Deploy via a production WSGI server and HTTPS, not Flask's development server; provision FFmpeg, Node.js if needed, storage and a cleanup worker.
- Move job state from in-memory Python dictionaries to Redis or a real queue if scaling beyond a single worker; enforce authentication/entitlement if paid rewards become a requirement.
- Add per-IP/network rate limiting, concurrency limits across instances, egress/firewall restrictions, domain/redirect checks, request timeouts, abuse monitoring, download quotas for infrastructure safety, and storage budget alerts. Host allowlisting alone is **not** a full server-side request forgery (SSRF) defense.
- Add legal operator contact details, copyright/abuse reporting, appropriate cookie-consent tooling, retention disclosures and reviewed legal terms. Confirm legal and platform-policy compliance for all use cases.
- Update dependencies frequently: platforms routinely change video extraction. Private or DRM-protected media is not supported. High-definition output depends on source availability; the project does not guarantee watermark removal.
- Add production tests (including provider mocks and media download end-to-end tests) and monitor actual failures with authorized media links.

## Why use Python?

Browsers cannot fetch and convert arbitrary video URLs from major social networks reliably because of cross-origin access restrictions and media formats. Python runs the server-side extractor; FFmpeg handles media merging/conversion. You still build the visible website using only HTML, CSS and JavaScript.

---

Made as the initial SnapMedia project. You can improve it feature by feature while learning HTML, CSS, JavaScript and Python.
