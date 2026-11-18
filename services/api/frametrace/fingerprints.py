"""Exact Hamming-neighbor candidate lookup for the current 64-bit representation.

Ten disjoint blocks guarantee any pair within nine differing bits shares a block.
The block index only prunes comparisons; exact distance and temporal verification remain
mandatory. This is an in-memory per-reference index, not a distributed vector database.
"""

VERSION = "dhash64-v1-fps2"
INDEX_VERSION = "exact-block-hamming64-r9-v1"
MAX_DISTANCE = 9
BLOCKS = tuple(
    (shift, (1 << width) - 1)
    for shift, width in [
        (0, 7),
        (7, 7),
        (14, 7),
        (21, 7),
        (28, 6),
        (34, 6),
        (40, 6),
        (46, 6),
        (52, 6),
        (58, 6),
    ]
)


def parse_hash(value):
    if not isinstance(value, str) or len(value) != 16:
        raise ValueError("Expected a 64-bit hexadecimal fingerprint")
    if any(char not in "0123456789abcdefABCDEF" for char in value):
        raise ValueError("Expected a 64-bit hexadecimal fingerprint")
    return int(value, 16)


class FingerprintIndex:
    def __init__(self, frames):
        self.frames = frames
        self.hashes = [parse_hash(frame["hash"]) for frame in frames]
        self.blocks = [{} for _ in BLOCKS]
        for index, value in enumerate(self.hashes):
            for bucket, (shift, mask) in zip(self.blocks, BLOCKS):
                bucket.setdefault((value >> shift) & mask, []).append(index)

    def neighbors(self, value):
        candidates = set()
        for bucket, (shift, mask) in zip(self.blocks, BLOCKS):
            candidates.update(bucket.get((value >> shift) & mask, ()))
        for index in sorted(candidates):
            distance = (value ^ self.hashes[index]).bit_count()
            if distance <= MAX_DISTANCE:
                yield self.frames[index], distance
