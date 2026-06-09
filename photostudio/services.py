import shutil
import subprocess
from pathlib import Path

from django.conf import settings


def generate_hls_for_video(video) -> None:
    video.hls_status = "processing"
    video.hls_error = ""
    video.save(update_fields=["hls_status", "hls_error"])

    source_path = Path(video.video.path)
    output_dir = Path(settings.MEDIA_ROOT) / "photostudio" / "videos" / "hls" / str(video.pk)
    playlist_path = output_dir / "master.m3u8"
    segment_pattern = output_dir / "segment_%03d.ts"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-profile:v",
        "baseline",
        "-level",
        "3.0",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-b:a",
        "128k",
        "-hls_time",
        "6",
        "-hls_playlist_type",
        "vod",
        "-hls_segment_filename",
        str(segment_pattern),
        str(playlist_path),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=1200)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        video.hls_status = "failed"
        video.hls_error = str(exc)[:2000]
        video.hls_playlist = ""
        video.save(update_fields=["hls_status", "hls_error", "hls_playlist"])
        return

    video.hls_status = "ready"
    video.hls_error = ""
    video.hls_playlist = playlist_path.relative_to(settings.MEDIA_ROOT).as_posix()
    video.save(update_fields=["hls_status", "hls_error", "hls_playlist"])
