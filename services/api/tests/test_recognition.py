import random

from frametrace.recognition import match


def frames(seed=42):
    rng = random.Random(seed)
    return [{"time": i / 2, "hash": f"{rng.getrandbits(64):016x}"} for i in range(40)]


def ref(data, identity="one"):
    return {
        "id": identity,
        "title": "Original fixture",
        "publisher": "FrameTrace test",
        "fingerprints": data,
        "source_url": None,
    }


def test_temporal_offset():
    data = frames()
    query = [dict(q, time=i / 2) for i, q in enumerate(data[8:20])]
    result = match(query, [ref(data)])
    assert result["classification"] == "matching_segment"
    assert result["candidates"][0]["start_seconds"] == 4
    assert result["candidates"][0]["source_url"] is None


def test_rejects_unknown_and_reordered_sequence():
    data = frames()
    assert match(frames(100)[:12], [ref(data)])["classification"] == "no_match"
    query = [dict(q, time=i / 2) for i, q in enumerate(reversed(data[8:20]))]
    assert match(query, [ref(data)])["classification"] == "no_match"


def test_duplicate_catalog_is_ambiguous():
    data = frames()
    assert match(data[:12], [ref(data), ref(data, "two")])["classification"] == "possible_match"


def test_repeated_shot_timestamp_is_ambiguous():
    data = frames()[:12]
    repeated = data + [dict(q, time=q["time"] + 6) for q in data]
    assert match(data, [ref(repeated)])["classification"] == "possible_match"


def test_blank_or_static_evidence_is_rejected():
    data = [{"time": i / 2, "hash": "123456789abcdef0"} for i in range(16)]
    assert match(data, [ref(data)])["classification"] == "no_match"
