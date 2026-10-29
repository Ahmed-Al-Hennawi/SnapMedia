"""Rebuild the offline design preview from the live website files."""
from __future__ import annotations

import base64
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build() -> None:
    page = (WEB / "index.html").read_text(encoding="utf-8")
    logo = data_uri(WEB / "snapmedia-logo.png", "image/png")
    favicon = data_uri(WEB / "favicon.svg", "image/svg+xml")
    css = (WEB / "styles.css").read_text(encoding="utf-8")
    css = css.replace("url('/snapmedia-logo.png')", f"url('{logo}')")
    page = page.replace('href="/favicon.svg"', f'href="{favicon}"')
    page = page.replace('src="/snapmedia-logo.png"', f'src="{logo}"')
    page = re.sub(r'^  <link rel="preconnect"[^\n]*\n', '', page, flags=re.MULTILINE)
    page = re.sub(r'^  <link href="https://fonts.googleapis.com[^\n]*\n', '', page, flags=re.MULTILINE)
    page = page.replace('  <link rel="stylesheet" href="/styles.css">', f'  <style>\n{css}\n  </style>')
    page = re.sub(r'^  <script src="/(?:i18n|config|ads|app)\.js" defer></script>\n', '', page, flags=re.MULTILINE)
    note = ('<p class="preview-note" role="note">Interactive design preview — video lookups and downloads are simulated. '
            'Run the Python server for real, authorized downloads.</p>')
    page = page.replace('        <div class="tool-wrap">', f'        {note}\n        <div class="tool-wrap">', 1)
    css_note = '.preview-note{max-width:600px;margin:-12px auto 22px;padding:10px 14px;border:1px solid #f59e0b80;border-radius:10px;background:#f59e0b17;color:var(--ink);font-size:11px;line-height:1.5}'
    page = page.replace('  </style>', f'\n{css_note}\n  </style>', 1)
    mock = """
window.fetch = async function(path, options) {
  const url = JSON.parse(options?.body || '{}').url || 'https://youtube.com/shorts/demo';
  const platform = /tiktok/i.test(url) ? 'tiktok' : /instagram/i.test(url) ? 'instagram' : /facebook|fb.watch/i.test(url) ? 'facebook' : 'youtube';
  const payload = path.includes('/api/info') ? {platform, url, title:'SnapMedia demo video — design preview only', uploader:'Sample Creator · Not a real lookup', duration:38, thumbnail:''} :
    path.includes('/api/download') ? {id:'abcdef0123456789abcdef0123456789', status:'queued'} :
    path.includes('/api/jobs/') ? {status:'ready', progress:100, filename:'demo.mp4', download_url:'/api/files/demo'} :
    {error:'This is a local design preview.'};
  return {ok:!payload.error, status:payload.error ? 400 : 200, json:async()=>payload};
};
const realClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function() {
  if (this.href.includes('/api/files/')) {
    const note = document.getElementById('form-status');
    note.hidden = false;
    note.textContent = 'Preview completed — no media was downloaded. Run the Python server for real downloads.';
  } else { return realClick.apply(this, arguments); }
};
"""
    scripts = [mock] + [(WEB / f"{name}.js").read_text(encoding="utf-8") for name in ("i18n", "config", "ads", "app")]
    page = page.replace('</body>', ''.join(f'<script>\n{script}\n</script>\n' for script in scripts) + '</body>')
    (ROOT / "SnapMedia-Interactive-Demo.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    build()
