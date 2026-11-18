"""Deterministic synthetic diagnostics; never use as a product accuracy claim."""

import argparse
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np
from frametrace.fingerprints import INDEX_VERSION, VERSION
from frametrace.media import extract
from frametrace.recognition import match

POSITIVES = [
    "clean",
    "compressed",
    "cropped",
    "captioned",
    "mirrored",
    "rotated",
    "speed_up",
    "letterboxed",
]
NEGATIVES = ["negative", "negative_other"]


def score_result(result, expected_reference, expected_seconds=4.0, tolerance=0.5):
    candidate = next(iter(result.get("candidates", [])), None)
    if expected_reference is None:
        rejected = result.get("classification") == "no_match" and not result.get(
            "candidates", []
        )
        return {
            "top_1_source_correct": None,
            "localized_correctly": None,
            "timestamp_error_seconds": None,
            "confirmed_correctly": None,
            "correct_decision": rejected,
        }
    source_correct = bool(
        candidate and candidate.get("reference_id") == expected_reference
    )
    seconds = candidate.get("start_seconds") if candidate else None
    error = (
        abs(seconds - expected_seconds)
        if source_correct
        and isinstance(seconds, (int, float))
        and not isinstance(seconds, bool)
        and math.isfinite(seconds)
        else None
    )
    localized = error is not None and error <= tolerance
    confirmed = localized and result.get("classification") == "matching_segment"
    return {
        "top_1_source_correct": source_correct,
        "localized_correctly": localized,
        "timestamp_error_seconds": error,
        "confirmed_correctly": confirmed,
        "correct_decision": confirmed,
    }


def benchmark(folder):
    references = []
    for name, identity in [
        ("reference", "synthetic-42"),
        ("reference_other", "synthetic-99"),
    ]:
        _, fingerprints = extract(folder / f"{name}.mp4", 60)
        references.append(
            {
                "id": identity,
                "title": identity,
                "publisher": "FrameTrace",
                "source_url": None,
                "fingerprints": fingerprints,
                "fingerprint_version": VERSION,
            }
        )
    rows = []
    hashes = {}
    for name in ["reference", "reference_other", *POSITIVES, *NEGATIVES]:
        with (folder / f"{name}.mp4").open("rb") as source:
            hashes[f"{name}.mp4"] = hashlib.file_digest(source, "sha256").hexdigest()
    for name in [*POSITIVES, *NEGATIVES]:
        start = time.perf_counter()
        _, query = extract(folder / f"{name}.mp4", 30)
        result = match(query, references)
        positive = name in POSITIVES
        rows.append(
            {
                "case": name,
                "classification": result["classification"],
                "expected_reference": "synthetic-42" if positive else None,
                "expected_start_seconds": 4 if positive else None,
                **score_result(result, "synthetic-42" if positive else None),
                "latency_seconds": round(time.perf_counter() - start, 4),
                "result": result,
            }
        )
    positives = [row for row in rows if row["expected_reference"]]
    negatives = [row for row in rows if row["expected_reference"] is None]
    return {
        "report_version": 2,
        "scope": "Original synthetic development fixtures, two-reference catalog; no independent holdout or real-world accuracy claim.",
        "fingerprint_version": VERSION,
        "retrieval_implementation": INDEX_VERSION,
        "timestamp_tolerance_seconds": 0.5,
        "positive_cases": len(positives),
        "negative_cases": len(negatives),
        "top_1_retrieval": sum(row["top_1_source_correct"] for row in positives)
        / len(positives),
        "localized_retrieval": sum(row["localized_correctly"] for row in positives)
        / len(positives),
        "confirmed_localized_retrieval": sum(
            row["confirmed_correctly"] for row in positives
        )
        / len(positives),
        "out_of_catalog_rejection": sum(row["correct_decision"] for row in negatives)
        / len(negatives),
        "p50_latency_seconds": float(
            np.percentile([r["latency_seconds"] for r in rows], 50)
        ),
        "p95_latency_seconds": float(
            np.percentile([r["latency_seconds"] for r in rows], 95)
        ),
        "latency_scope": "Local decode, feature extraction, temporary per-reference index construction and matching; excludes reference decoding, network, queue and upload.",
        "runtime": {
            "opencv": cv2.__version__,
            "numpy": np.__version__,
            "ffmpeg": subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, check=True
            ).stdout.splitlines()[0],
        },
        "input_sha256": hashes,
        "cases": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--check-core",
        action="store_true",
        help="Require clean localization and both unknown rejections; edited-case failures remain visible diagnostics",
    )
    args = parser.parse_args()
    report = benchmark(args.folder)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in {"cases", "input_sha256"}},
            indent=2,
        )
    )
    if args.check_core and not all(
        row["correct_decision"]
        for row in report["cases"]
        if row["case"] in {"clean", *NEGATIVES}
    ):
        raise SystemExit("Core recognition regression: inspect the saved report.")


if __name__ == "__main__":
    main()
