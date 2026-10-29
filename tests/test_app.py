"""Run with `python -m pytest -q` after installing requirements and pytest."""
import pytest
import shutil
import subprocess

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
    assert client.get('/api/health').json['ok'] is True
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
