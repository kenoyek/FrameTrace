"""Small deterministic integration benchmark; never use as a product accuracy claim."""

import argparse
import json
import time
from pathlib import Path

import numpy as np
from frametrace.media import extract
from frametrace.recognition import match


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _, fingerprints = extract(args.folder / "reference.mp4", 60)
    reference = {
        "id": "synthetic-42",
        "title": "Generated fixture 42",
        "publisher": "FrameTrace",
        "source_url": None,
        "fingerprints": fingerprints,
    }
    rows = []
    for name in ["clean", "compressed", "cropped", "captioned", "negative"]:
        start = time.perf_counter()
        _, query = extract(args.folder / f"{name}.mp4", 30)
        result = match(query, [reference])
        candidate = next(iter(result["candidates"]), None)
        expected_match = name != "negative"
        rows.append(
            {
                "case": name,
                "classification": result["classification"],
                "expected_match": expected_match,
                "correct_decision": bool(candidate) == expected_match,
                "timestamp_error_seconds": abs(candidate["start_seconds"] - 4)
                if candidate and expected_match
                else None,
                "latency_seconds": round(time.perf_counter() - start, 4),
                "result": result,
            }
        )
    positives = [r for r in rows if r["expected_match"]]
    report = {
        "scope": "Original synthetic development fixtures only; no holdout or real-world accuracy claim.",
        "fingerprint_version": "dhash64-v1-fps2",
        "top_1_retrieval": sum(r["correct_decision"] for r in positives)
        / len(positives),
        "out_of_catalog_rejection": float(rows[-1]["correct_decision"]),
        "p50_latency_seconds": float(
            np.percentile([r["latency_seconds"] for r in rows], 50)
        ),
        "p95_latency_seconds": float(
            np.percentile([r["latency_seconds"] for r in rows], 95)
        ),
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
