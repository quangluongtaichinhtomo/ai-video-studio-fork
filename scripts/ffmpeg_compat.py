"""ffmpeg version shims shared by the Python scripts.

Long filtergraphs are written to a file and read back by ffmpeg. The option for that changed in ffmpeg 7.0:
  ffmpeg >= 7:  -/filter_complex <file>        (generic "-/<option>" = read the option's value from a file)
  ffmpeg <= 6:  -filter_complex_script <file>  (deprecated in 7, still accepted there)
ffmpeg 6.1 (Ubuntu 24.04) rejects "-/filter_complex" ("Option not found", exit status 8), so the flag is picked
from the installed version, read once per process.
"""
import functools
import re
import subprocess


def major_from_version_text(text):
    """Major release (6, 7, 8...) from `ffmpeg -version` output, or None if it can't be read."""
    m = re.search(r"ffmpeg version n?(\d+)\.\d", text)
    if m:
        return int(m.group(1))
    # Git / nightly builds ("N-113000-g...", "2024-03-07-git-...") carry no release number:
    # libavutil major 58 = ffmpeg 6.x, 59 = 7.x, 60 = 8.x.
    m = re.search(r"^\s*libavutil\s+(\d+)\.", text, re.M)
    return int(m.group(1)) - 52 if m else None


@functools.lru_cache(maxsize=None)
def ffmpeg_major():
    """Major release of the `ffmpeg` on PATH, or None when it can't be run or its version can't be read."""
    try:
        out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, errors="replace").stdout
    except OSError:
        return None
    return major_from_version_text(out)


def filter_complex_file_args(path):
    """ffmpeg args that read the -filter_complex graph from `path`, for the installed ffmpeg."""
    major = ffmpeg_major()
    if major is not None and major < 7:
        return ["-filter_complex_script", path]
    return ["-/filter_complex", path]
