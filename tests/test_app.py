"""Run with `python -m pytest -q` after installing requirements and pytest."""
import pytest
import shutil
import subprocess
import importlib
import time
import os

pytest.importorskip("flask")
pytest.importorskip("yt_dlp")
from app import app, identify_url, InputError, nice_filename, compatible_mp4, media_streams


@pytest.mark.parametrize('url,platform', [
    ('https://www.tiktok.com/@author/video/123', 'tiktok'),
    ('https://vm.tiktok.com/ZTest/', 'tiktok'),
    ('https://www.instagram.com/reel/abc/', 'instagram'),
    ('https://youtube.com/shorts/abc', 'youtube'),
    ('https://youtu.be/abc', 'youtube'),
    ('https://www.facebook.com/reel/123', 'facebook'),
    ('https://fb.watch/ab/', 'facebook'),
])
def test_supported_urls(url, platform):
    assert identify_url(url)[0] == platform


@pytest.mark.parametrize('url', [
    'http://youtube.com/watch?v=123',
    'https://youtube.com.attacker.test/watch?v=123',
    'https://youtube.com@127.0.0.1/private',
    'file:///etc/passwd',
    'https://127.0.0.1/internal',
    'https://localhost/admin',
    'https://youtube.com:4444/watch?v=123',
    'https://instagram.com/',
    'javascript:alert(1)',
    'https://facebook.com\\@attacker.test/evil',
])
def test_reject_bad_urls(url):
    with pytest.raises(InputError):
        identify_url(url)


def test_query_strip_fragment():
    platform, url = identify_url('https://www.youtube.com/watch?v=123#fragment')
    assert platform == 'youtube' and url.endswith('?v=123')


def test_file_name_sanitization():
    result = nice_filename('../cat: <video>/?', 'mp4')
    assert '/' not in result and ':' not in result and result.endswith('.mp4')


def test_health_and_input_rejection():
    client = app.test_client()
    health = client.get('/api/health').json
    assert health['ok'] is True
    assert health['media_pipeline'] == 'h264-aac-verified'
    assert isinstance(health['h264_encoder'], bool)
    result = client.post('/api/info', json={'url':'https://example.com/malicious'})
    assert result.status_code == 422
    assert 'error' in result.json


def test_static_pages():
    client = app.test_client()
    for url in ['/', '/terms', '/privacy', '/styles.css', '/app.js']:
        result = client.get(url)
        assert result.status_code == 200


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'), reason='FFmpeg is unavailable')
def test_mp4_is_converted_to_playable_codecs(tmp_path):
    source = tmp_path / 'sample.mp4'
    subprocess.run([
        'ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=64x64:rate=2',
        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-t', '1',
        '-c:v', 'mpeg4', '-c:a', 'aac', '-shortest', str(source),
    ], check=True)
    output = compatible_mp4(source)
    streams = media_streams(output)
    assert output.suffix == '.mp4' and output.stat().st_size > 0
    assert any(s.get('codec_type') == 'video' and s.get('codec_name') == 'h264'
               and s.get('pix_fmt') == 'yuv420p' for s in streams)
    assert any(s.get('codec_type') == 'audio' and s.get('codec_name') == 'aac' for s in streams)


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'), reason='FFmpeg is unavailable')
def test_download_job_serves_the_converted_video(tmp_path, monkeypatch):
    module = importlib.import_module('app')
    source = tmp_path / 'source.mp4'
    subprocess.run([
        'ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=64x64:rate=2',
        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-t', '1',
        '-c:v', 'mpeg4', '-c:a', 'aac', '-shortest', str(source),
    ], check=True)

    class LocalDownload:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def extract_info(self, _url, download):
            assert download
            target = self.options['outtmpl'].replace('%(ext)s', 'mp4')
            shutil.copyfile(source, target)

    monkeypatch.setattr(module, 'YoutubeDL', LocalDownload)
    monkeypatch.setattr(module, 'DOWNLOAD_DIR', tmp_path / 'downloads')
    monkeypatch.setattr(module, '_jobs', {})
    job_id = 'a' * 32
    module._jobs[job_id] = {'created': time.time(), 'status': 'queued', 'progress': 0}
    module.do_download(job_id, {'url': 'https://example.test/video', 'title': 'Sample'}, 'mp4', 'standard')

    job = module._jobs[job_id]
    assert job['status'] == 'ready'
    assert job['file'].endswith('media-compatible.mp4')
    assert any(stream.get('codec_type') == 'video' and stream.get('codec_name') == 'h264'
               for stream in media_streams(job['file']))
    response = app.test_client().get(f'/api/files/{job_id}')
    assert response.status_code == 200
    assert response.mimetype == 'video/mp4'
    assert response.headers['Content-Disposition'].startswith('attachment;')


def test_old_download_folder_is_cleaned_after_restart(tmp_path, monkeypatch):
    module = importlib.import_module('app')
    orphan = tmp_path / ('b' * 32)
    orphan.mkdir()
    (orphan / 'media.mp4').write_bytes(b'old')
    old = time.time() - module.FILE_TTL_SECONDS - 60
    os.utime(orphan, (old, old))
    monkeypatch.setattr(module, 'DOWNLOAD_DIR', tmp_path)
    monkeypatch.setattr(module, '_jobs', {})
    module.clear_expired()
    assert not orphan.exists()
