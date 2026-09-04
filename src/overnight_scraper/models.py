from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class LookupOutcome(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    TRANSIENT_ERROR = "transient_error"
    PERMANENT_ERROR = "permanent_error"

@dataclass(frozen=True)
class Family:
    family_id: str
    representative_sku: str
    skus: tuple[str, ...]
    declared_sku_count: int

@dataclass
class ColorMedia:
    images: list[str] = field(default_factory=list)
    videos: list[str] = field(default_factory=list)
    available: Optional[bool] = None
    evidence: dict[str, Any] = field(default_factory=dict)

@dataclass
class Attempt:
    family_id: str
    sku: str
    url: Optional[str]
    outcome: LookupOutcome
    detail: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class FamilyResult:
    family_id: str
    source_sku: str
    product_url: str
    white: ColorMedia
    yellow_gold: ColorMedia = field(default_factory=ColorMedia)
    rose_gold: ColorMedia = field(default_factory=ColorMedia)
    attempts: list[Attempt] = field(default_factory=list)
    unrecognized_color_media: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
