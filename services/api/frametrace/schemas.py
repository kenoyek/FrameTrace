from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Stage = Literal[
    "queued",
    "extracting_features",
    "searching_catalog",
    "verifying_candidates",
    "completed",
    "failed",
]


class AcceptedJob(BaseModel):
    id: str
    access_token: str
    status: Stage


class Evidence(BaseModel):
    aligned_frames: int
    query_frames: int
    coverage: float
    mean_hash_distance: float


class Candidate(BaseModel):
    reference_id: str
    title: str
    publisher: str
    source_url: str | None
    start_seconds: float
    timestamp_uncertainty_seconds: float
    evidence: Evidence
    ranking_score: float
    attribution: Literal["indexed_reference"]


class RecognitionResult(BaseModel):
    classification: Literal["matching_segment", "possible_match", "no_match"]
    candidates: list[Candidate]
    reason: str
    elapsed_seconds: float | None = None


class RecognitionJob(BaseModel):
    id: str
    status: Stage
    result: RecognitionResult | None
    error: str | None


class HistoryItem(RecognitionJob):
    saved: bool
    created_at: datetime


class HistoryPage(BaseModel):
    items: list[HistoryItem]
    next_offset: int | None


class FavoriteResult(BaseModel):
    id: str
    saved: bool


class ClaimedJob(BaseModel):
    id: str


class ClearedHistory(BaseModel):
    deleted: int
    may_have_more: bool
