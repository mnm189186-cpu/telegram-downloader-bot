# downloader.py
import asyncio
import os
import shlex
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from config import DOWNLOADS_DIR, YTDLP_BINARY, FFMPEG_BINARY, MAX_FILE_SIZE_BYTES

# Simple wrapper around yt-dlp to download and optionally post-process
class DownloadResult:
    def __init__(self, filepath: Path, meta: Dict):
        self.filepath = filepath
        self.meta = meta

async def run_cmd(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 3600) -> Tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(cwd) if cwd else None,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "", f"Timeout after {timeout}s"
    return proc.returncode, out.decode(errors="ignore"), err.decode(errors="ignore")

async def ytdlp_info(url_or_query: str) -> Dict:
    # get metadata with yt-dlp --dump-json (handles searches if query starts with "ytsearch:")
    cmd = [YTDLP_BINARY, "--no-warnings", "--no-playlist", "--dump-single-json", url_or_query]
    code, out, err = await run_cmd(cmd)
    if code != 0:
        raise RuntimeError(f"yt-dlp info failed: {err or out}")
    import json
    return json.loads(out)

async def download_media(url: str, format_selector: Optional[str] = None, output_basename: Optional[str] = None, extract_audio: bool = False) -> DownloadResult:
    # unique temp dir per download
    uid = uuid.uuid4().hex
    workdir = DOWNLOADS_DIR / uid
    workdir.mkdir(parents=True, exist_ok=True)

    out_template = (output_basename or "%(title).200s-%(id)s") + ".%(ext)s"
    out_path = str(workdir / out_template)

    cmd = [
        YTDLP_BINARY,
        "-o", out_path,
        "--no-warnings",
        "--restrict-filenames",
        "--merge-output-format", "mp4",
    ]
    if format_selector:
        cmd += ["-f", format_selector]
    if extract_audio:
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]

    # attempt download
    code, out, err = await run_cmd(cmd + [url], cwd=workdir, timeout=3600)
    if code != 0:
        raise RuntimeError(f"yt-dlp download failed: {err or out}")

    # find downloaded file
    files = list(workdir.glob("*"))
    if not files:
        raise RuntimeError("No output file after yt-dlp")
    # pick largest file
    files_sorted = sorted(files, key=lambda p: p.stat().st_size, reverse=True)
    target = files_sorted[0]

    # check size
    if target.stat().st_size > MAX_FILE_SIZE_BYTES:
        # caller should decide (upload or cloud)
        return DownloadResult(filepath=target, meta={"warning": "file_too_large"})
    # try extract metadata via yt-dlp --skip-download --dump-json
    try:
        meta = await ytdlp_info(url)
    except Exception:
        meta = {}

    return DownloadResult(filepath=target, meta=meta)

# helper for trimming/format conversion using ffmpeg
async def ffmpeg_convert(input_path: Path, output_path: Path, extra_args: Optional[List[str]] = None) -> Tuple[bool, str]:
    args = [FFMPEG_BINARY, "-y", "-i", str(input_path)]
    if extra_args:
        args += extra_args
    args += [str(output_path)]
    code, out, err = await run_cmd(args, cwd=input_path.parent, timeout=1800)
    success = (code == 0)
    return success, err if not success else out
