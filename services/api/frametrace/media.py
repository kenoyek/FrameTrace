"""Local-only decoding: never pass client URLs or names to FFmpeg."""

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

from .config import settings


class InvalidMedia(ValueError):
    pass


def probe(path: Path, max_seconds: float) -> float:
    try:
        # Only ISO BMFF (MP4/MOV) containers enter the decoder in this first implementation.
        with path.open("rb") as stream:
            if stream.read(12)[4:8] != b"ftyp":
                raise InvalidMedia("Choose a valid MP4 or MOV video.")
        output = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-protocol_whitelist",
                "file",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(path.resolve()),
            ],
            capture_output=True,
            check=True,
            timeout=10,
        )
        metadata = json.loads(output.stdout)
        video = next(s for s in metadata["streams"] if s["codec_type"] == "video")
        duration = float(metadata["format"]["duration"])
        width, height = int(video["width"]), int(video["height"])
        if not np.isfinite(duration) or not 1 <= duration <= max_seconds:
            raise InvalidMedia(f"Video duration must be between 1 and {max_seconds:g} seconds.")
        if width <= 0 or height <= 0 or width * height > settings.max_pixels:
            raise InvalidMedia("Video resolution is unsupported.")
        return duration
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, StopIteration) as exc:
        if isinstance(exc, InvalidMedia):
            raise
        raise InvalidMedia("Video cannot be decoded safely.") from exc


def extract(path: Path, max_seconds: float) -> tuple[float, list[dict]]:
    duration = probe(path, max_seconds)
    try:
        output = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-nostdin",
                "-threads",
                "1",
                "-protocol_whitelist",
                "file",
                "-i",
                str(path.resolve()),
                "-an",
                "-sn",
                "-dn",
                "-vf",
                "fps=2,scale=160:90",
                "-t",
                str(max_seconds),
                "-threads",
                "1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "gray",
                "pipe:1",
            ],
            capture_output=True,
            check=True,
            timeout=settings.decoder_timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise InvalidMedia("Video extraction failed or exceeded the time limit.") from exc
    frames = np.frombuffer(output.stdout, dtype=np.uint8)
    if frames.size == 0 or frames.size % (160 * 90):
        raise InvalidMedia("Video contains no decodable frames.")
    hashes = []
    for index, frame in enumerate(frames.reshape(-1, 90, 160)):
        small = cv2.resize(frame, (9, 8), interpolation=cv2.INTER_AREA)
        # Reject almost static, blank evidence rather than accepting common black frames.
        if float(frame.std()) < 8:
            continue
        bits = (small[:, 1:] > small[:, :-1]).flatten()
        fingerprint = sum(int(bit) << shift for shift, bit in enumerate(bits))
        hashes.append({"time": index / 2, "hash": f"{fingerprint:016x}"})
    return duration, hashes
