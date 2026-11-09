"""Deterministic original synthetic footage; no downloaded copyrighted media.

These are algorithm integration fixtures, not a real-world accuracy benchmark.
"""

import argparse
import subprocess
from pathlib import Path

import cv2
import numpy as np


def video(path: Path, seed: int, seconds: int = 16):
    rng = np.random.default_rng(seed)
    # Continuous independently moving shapes keep adjacent samples related while
    # providing distinctive temporal evidence instead of random per-frame noise.
    centers = rng.integers(0, 240, (30, 2)).astype(float)
    velocities = rng.uniform(-50, 50, (30, 2))
    colors = rng.integers(30, 255, (30, 3))
    encoder = subprocess.Popen(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            "320x240",
            "-r",
            "12",
            "-i",
            "pipe:0",
            "-an",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        stdin=subprocess.PIPE,
    )
    try:
        for frame in range(seconds * 12):
            image = np.zeros((240, 320, 3), np.uint8)
            for i, (center, velocity, color) in enumerate(
                zip(centers, velocities, colors)
            ):
                point = (center + velocity * frame / 12) % [320, 240]
                cv2.circle(
                    image,
                    tuple(point.astype(int)),
                    9 + i % 15,
                    tuple(int(c) for c in color),
                    -1,
                )
            cv2.putText(
                image,
                f"FrameTrace fixture {seed}",
                (8, 230),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (210, 210, 210),
                1,
            )
            encoder.stdin.write(image.tobytes())
    finally:
        encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError("Fixture encoding failed")


def fixtures(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    for name, seed in [("reference", 42), ("negative", 73)]:
        video(folder / f"{name}.mp4", seed)
    for name, extra in [
        ("clean", []),
        ("compressed", ["-vf", "scale=160:120", "-crf", "32"]),
        ("cropped", ["-vf", "crop=240:200:40:20"]),
        ("captioned", ["-vf", "drawbox=x=0:y=200:w=320:h=25:color=white:t=fill"]),
    ]:
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-ss",
                "4",
                "-i",
                str(folder / "reference.mp4"),
                "-t",
                "6",
                "-an",
                "-c:v",
                "libx264",
                "-threads",
                "1",
                *extra,
                str(folder / f"{name}.mp4"),
            ],
            check=True,
        )

    for asset in folder.glob("*.mp4"):
        asset.chmod(0o644)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    fixtures(parser.parse_args().folder)
