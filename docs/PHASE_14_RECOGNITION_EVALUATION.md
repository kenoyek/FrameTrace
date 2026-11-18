# Recognition evaluation corrections and edit diagnostics — 18 November 2026

The old benchmark treated any candidate as a correct positive decision. It did not check
reference identity, localization tolerance or whether the API confirmed a match. Scoring
now separates correct top-one source, localization within 0.5 seconds, and confirmed
localized recognition. Possible matches do not count as confirmations. Unknown rejection
requires no_match with an empty candidate list. Wrong sources, wrong/nonfinite timestamps
and contradictory candidate/classification combinations cannot earn a correct decision.

The fixture generator now produces two original synthetic catalog references (seeds 42/99),
eight source-present query variants and two six-second out-of-catalog originals (73/107).
Source-present variants start at source second four. Added transforms are horizontal mirror,
90-degree rotation, 1.25x speed and letterboxing, alongside clean/compression/crop/caption.
These are generated local files, not downloaded media. There is no audio signal to evaluate.

## Actual decoded-media results

The version 2 report is docs/benchmark-expanded-development.json. Both catalog references
and all query files were decoded with the actual media extractor and matcher. No production
matcher thresholds or ranking rules changed to improve these numbers.

| Query case | Observed result | Source/time correct and confirmed |
| --- | --- | --- |
| Clean | matching_segment | Yes, offset 4.0 seconds |
| Compressed | matching_segment | Yes, offset 4.0 seconds |
| Captioned | matching_segment | Yes, offset 4.0 seconds |
| Cropped | no_match | No |
| Mirrored | no_match | No |
| Rotated | no_match | No |
| Speed-up | no_match | No |
| Letterboxed | no_match | No |
| Unknown 73 | no_match | Correct rejection |
| Unknown 107 | no_match | Correct rejection |

Confirmed localization is **3/8**, and unknown rejection **2/2**, for these cases only.
The dataset is tiny, synthetic, familiar development material, with a two-reference
exhaustive catalog. It is not an independent holdout, licensed real-world benchmark,
product accuracy estimate or evidence of broad edit robustness. The five missed edit
classes remain matcher limitations. The original v1 report is retained as historical
evidence; its any-candidate scoring and smaller corpus make direct rate comparisons invalid.

The report records input SHA256 values, OpenCV/NumPy/FFmpeg versions, full per-case evidence,
case counts and timestamp tolerance. Latencies cover local decoding, feature extraction
and matching, excluding reference indexing, upload, queueing and network. They depend on
hardware/tool versions and are not an SLO. File hashes help identify exact inputs; codec
outputs/latencies are not promised bit-identical across toolchain versions.

## Regression gates and validation

`--check-core` fails only when clean source/timestamp confirmation or either unknown
rejection regresses. Other edited-case failures remain visible diagnostics, not passing
robustness tests. The report is written before gate failure. CI now regenerates media,
runs these checks and uploads its JSON report for 14 days, including available failure
reports. Local success does not claim that GitHub CI has run successfully.

All 66 backend tests passed, with one PostgreSQL-only test skipped. Five scoring tests
cover wrong sources, wrong timestamps, possible matches, unknown rejection and invalid
numeric timestamps. Real fixture generation/decoding/benchmark core gates passed; Python
lint/format, workflow YAML parsing and diff checks passed. Mobile source was unchanged,
so mobile bundles/device tests were not rerun. No APK or native-device acceptance is claimed.
Existing native-build, hosted rollout and dependency-security release gates remain open.

```sh
.venv/bin/python scripts/make_fixtures.py var/evaluation-fixtures
.venv/bin/python packages/evaluation/benchmark.py var/evaluation-fixtures --output var/benchmark.json --check-core
```
