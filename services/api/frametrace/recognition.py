"""Conservative fingerprint retrieval with constant-offset sequence verification.

Scores are evidence measures, never calibrated probabilities. This matcher is
for a small controlled catalog; cropped/replaced scenes require later providers.
"""

from collections import defaultdict


def match(query: list[dict], references: list[dict]) -> dict:
    candidates = []
    if len(query) < 6 or len({q["hash"] for q in query}) < 4:
        return {
            "classification": "no_match",
            "candidates": [],
            "reason": "Insufficient distinctive temporal evidence.",
        }
    for ref in references:
        votes: dict[float, dict[int, tuple[int, float]]] = defaultdict(dict)
        frames = ref["fingerprints"]
        for qi, q in enumerate(query):
            for r in frames:
                distance = (int(q["hash"], 16) ^ int(r["hash"], 16)).bit_count()
                offset = round((r["time"] - q["time"]) * 2) / 2
                if distance <= 9 and offset >= 0:
                    previous = votes[offset].get(qi)
                    if previous is None or distance < previous[0]:
                        votes[offset][qi] = (distance, r["time"])
        # Preserve alternative offsets: repeated scenes are an ambiguity, not an exact timestamp.
        for offset, aligned in votes.items():
            coverage = len(aligned) / len(query)
            span = max(aligned) - min(aligned)
            if len(aligned) < 6 or coverage < 0.65 or span / 2 < 2.5:
                continue
            mean_distance = sum(v[0] for v in aligned.values()) / len(aligned)
            candidates.append(
                {
                    "reference_id": ref["id"],
                    "title": ref["title"],
                    "publisher": ref["publisher"],
                    "source_url": ref.get("source_url"),
                    "start_seconds": offset,
                    "timestamp_uncertainty_seconds": 0.5,
                    "evidence": {
                        "aligned_frames": len(aligned),
                        "query_frames": len(query),
                        "coverage": round(coverage, 3),
                        "mean_hash_distance": round(mean_distance, 2),
                    },
                    "ranking_score": coverage * (1 - mean_distance / 64),
                    "attribution": "indexed_reference",
                }
            )
    candidates.sort(key=lambda c: (-c["ranking_score"], c["reference_id"], c["start_seconds"]))
    if not candidates:
        return {
            "classification": "no_match",
            "candidates": [],
            "reason": "No temporally consistent match in the active reference catalog.",
        }
    best = candidates[0]
    ambiguous = (
        len(candidates) > 1 and best["ranking_score"] - candidates[1]["ranking_score"] < 0.08
    )
    classification = (
        "possible_match" if ambiguous or best["evidence"]["coverage"] < 0.85 else "matching_segment"
    )
    return {
        "classification": classification,
        "candidates": candidates[:5],
        "reason": "Multiple plausible alignments."
        if ambiguous
        else "Consecutive visual fingerprints align to an indexed recording; original ownership is unverified.",
    }
