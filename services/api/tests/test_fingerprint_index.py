import random

import pytest

from frametrace.fingerprints import BLOCKS, FingerprintIndex, parse_hash
from frametrace.recognition import match


def test_index_matches_exhaustive_neighbors_for_seeded_queries():
    rng = random.Random(20261118)
    hashes = [rng.getrandbits(64) for _ in range(200)]
    frames = [{"time": n / 2, "hash": f"{value:016x}"} for n, value in enumerate(hashes)]
    index = FingerprintIndex(frames)
    for n in range(100):
        original = hashes[n]
        for radius in (0, 1, 5, 9, 10, 20):
            flips = rng.sample(range(64), radius)
            query = original
            for bit in flips:
                query ^= 1 << bit
            expected = [
                (frame, (value ^ query).bit_count())
                for frame, value in zip(frames, hashes)
                if (value ^ query).bit_count() <= 9
            ]
            assert list(index.neighbors(query)) == expected


def test_blocks_partition_all_64_bits_and_duplicate_frames_remain_distinct():
    masks = [mask << shift for shift, mask in BLOCKS]
    assert sum(masks) == (1 << 64) - 1
    assert len(BLOCKS) == 10
    frames = [{"time": 0, "hash": "0" * 16}, {"time": 1, "hash": "0" * 16}]
    assert len(list(FingerprintIndex(frames).neighbors(0))) == 2


@pytest.mark.parametrize("value", ["", "f" * 17, "-000000000000001", "g" * 16, 10, None])
def test_rejects_invalid_fingerprint_representations(value):
    with pytest.raises(ValueError):
        parse_hash(value)


def test_explicitly_incompatible_reference_is_never_matched():
    rng = random.Random(42)
    query = [{"time": n / 2, "hash": f"{rng.getrandbits(64):016x}"} for n in range(12)]
    ref = {
        "id": "old",
        "title": "Unsupported",
        "publisher": "Test",
        "fingerprints": query,
        "fingerprint_version": "different-v2",
    }
    assert match(query, [ref])["classification"] == "no_match"
    ref["fingerprint_version"] = "dhash64-v1-fps2"
    assert match(query, [ref])["classification"] == "matching_segment"
