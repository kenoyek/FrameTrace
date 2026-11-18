# Exact fingerprint candidate indexing — 18 November 2026

The matcher now parses each 64-bit hash once and builds a temporary block index per
reference instead of comparing every query frame to every reference frame. It partitions
all 64 bits into ten disjoint blocks. A pair with at most nine differing bits must share
at least one block, so its exact neighbor cannot be lost by candidate pruning. Candidate
hashes still undergo full Hamming distance checking at the unchanged nine-bit threshold.
Order, temporal offset voting, coverage, ambiguity and localization rules remain unchanged.
Duplicate frames remain distinct; candidate frame indices are sorted to preserve baseline
traversal. Hash parsing validates the existing 16-hex-character representation.

This is an in-memory, per-reference index rebuilt per job, not a persisted/global vector
index. The worker still loads/searches every supported active catalog reference. It adds
roughly ten bucket memberships per reference frame and trades memory/index construction
for fewer pair comparisons. No throughput, reduced end-to-end latency or large-catalog
capacity is established by the tiny fixture run.

Worker SQL now excludes references whose fingerprint_version is not dhash64-v1-fps2.
The matcher also skips explicitly incompatible versions; ingestion explicitly records the
current version. Internal reference dictionaries omitting version retain the current-format
fallback for compatibility with existing callers/tests. No stored fingerprints or schema
were migrated. Operators must reindex using a future version's actual extractor before
changing a version label; relabeling incompatible fingerprints does not convert them.

## Evidence

- All 75 backend tests passed, with one PostgreSQL-only concurrency case skipped.
- Nine new cases cover exhaustive-neighbor parity across 600 seeded query variants,
  distances including 9/10 bits, complete 64-bit partitioning, duplicate frames, invalid
  hash representations and explicit version mismatch rejection.
- The actual ten-video benchmark ran against the same SHA256-identical files used in
  phase 14. All ten complete results, candidates and evidence exactly matched the saved
  exhaustive baseline. The new report is docs/benchmark-indexed-development.json and
  records the retrieval implementation identifier and accurate timing scope.
- Core clean/unknown regression gates passed. Three of eight source-present edits still
  confirm source/timestamp; both unknowns reject. The five missed edit classes remain
  unsolved. No accuracy improvement or real-world holdout performance is claimed.
- Python lint/format and diff checks passed. Mobile source was unchanged and mobile/device
  checks were not rerun. No native APK artifact or hosted rollout is claimed.

The mathematical radius guarantee depends on these ten blocks and the nine-bit threshold;
changing either requires revisiting the index and its exhaustive parity tests. Broader
catalog/load benchmarks, a persisted index strategy, diverse authorized media and strict
holdout evaluation remain future acceptance work. Native build/device and dependency
security gates remain open.
