"""Future multimodal implementations must preserve timestamps and model versions.

No unavailable provider is represented as a successful recognition signal.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TimedEmbedding:
    seconds: float
    values: tuple[float, ...]
    model_version: str


class EmbeddingProvider(Protocol):
    def embed(self, media: Path) -> list[TimedEmbedding]: ...


@dataclass(frozen=True)
class TranscriptSegment:
    start_seconds: float
    end_seconds: float
    text: str
    language: str


class SpeechProvider(Protocol):
    def transcribe(self, media: Path) -> list[TranscriptSegment]: ...
