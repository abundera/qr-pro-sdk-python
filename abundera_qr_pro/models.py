from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Code:
    id: str
    slug: str
    destination_url: str
    created_at: str
    updated_at: str
    active: bool
    short_url: str
    label: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    group_id: Optional[str] = None
    scan_count: Optional[int] = None
    last_scan_at: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "Code":
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__ if k in d})


@dataclass
class CodeCreate:
    destination_url: str
    slug: Optional[str] = None
    label: Optional[str] = None
    tags: Optional[List[str]] = None
    group_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class CodePatch:
    destination_url: Optional[str] = None
    label: Optional[str] = None
    tags: Optional[List[str]] = None
    group_id: Optional[str] = None
    active: Optional[bool] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Group:
    id: str
    name: str
    created_at: str
    description: Optional[str] = None
    code_count: Optional[int] = None


@dataclass
class Webhook:
    id: str
    url: str
    events: List[str]
    active: bool
    created_at: str
    secret: Optional[str] = None  # only returned on creation


@dataclass
class Analytics:
    code_id: str
    total_scans: int
    unique_days: int
    by_day: List[dict]
    by_country: List[dict]
    by_device: List[dict]


@dataclass
class ListResult(Generic[T]):
    data: List[T]
    pagination: dict


@dataclass
class ApiError:
    status: int
    code: str
    message: str
    request_id: Optional[str] = None
    raw: Optional[Any] = None
