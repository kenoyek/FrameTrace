# Recognition engine

1. Accept local MP4/MOV (ISO BMFF signature); FFprobe verifies video dimensions and duration.
2. FFmpeg reads only local file protocols, strips audio/subtitles/data from extraction,
   limits threads/time/duration and samples at two frames per second, 160×90 grayscale.
3. Skip nearly blank frames; compute 64-bit horizontal difference hashes (9×8 downsample).
4. Retrieve frame correspondences at Hamming distance ≤9. Vote by source-minus-query
   offset on a half-second grid.
5. Require at least six corresponding samples, ≥65% coverage and ≥2.5 seconds temporal
   span at one offset. Reject low-diversity sequences. ≥85% coverage with clear candidate
   separation is labeled matching_segment; ambiguity is possible_match.
6. Retain competing offsets and recordings. Results identify an indexed recording, never
   verified authorship. Ranking scores are heuristic evidence, not probability percentages.

Temporal assumptions: unmodified speed and predominantly forward playback. Sampling
uncertainty is at least ±0.5s. Source alignment finer than this is not claimed.

Version: `dhash64-v1-fps2`. JSON fingerprints and exhaustive pair comparison are suitable
only for a tiny reference catalog. Model/index changes must trigger explicit reindexing.

The development benchmark uses original deterministic shapes, a six-second excerpt at
four seconds, recompression/downscale, caption bar, crop and unrelated footage. Cropping
currently fails. See docs/benchmark-development.json for measured output. No speech,
audio, OCR, scene detection, embeddings, speed-change/crop robustness, title guessing,
external video downloads or calibrated confidence is implemented.
