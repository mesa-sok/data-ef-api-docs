"""
Events-and-News Pydantic models.

The OpenAPI spec marks every response as ``{}`` so models use
``extra="allow"`` and all fields are optional.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EventsAndNewsList(BaseModel):
    """A single article summary as it appears in a list response."""

    model_config = {"extra": "allow"}

    id: str | int | None = None
    slug: str | None = None
    title_en: str | None = None
    title_kh: str | None = None
    summary_en: str | None = None
    summary_kh: str | None = None
    category: str | None = None
    event_date: str | None = None
    thumbnail: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class EventsAndNewsListData(BaseModel):
    """Inner paginated wrapper returned by the list endpoint."""

    model_config = {"extra": "allow"}

    results: list[EventsAndNewsList] | None = None
    total: int | None = None
    page: int | None = None
    size: int | None = None
    total_pages: int | None = None


class EventsAndNewsListResponse(BaseModel):
    """Response envelope for ``GET /api/v1/events-and-news``."""

    model_config = {"extra": "allow"}

    data: EventsAndNewsListData | None = None


class EventsAndNewsDetail(BaseModel):
    """Full article returned by ``GET /api/v1/events-and-news/{slug}``.

    Many content fields may be absent depending on category and locale.
    """

    model_config = {"extra": "allow"}

    id: str | int | None = None
    slug: str | None = None
    title_en: str | None = None
    title_kh: str | None = None
    body_en: str | None = None
    body_kh: str | None = None
    summary_en: str | None = None
    summary_kh: str | None = None
    category: str | None = None
    event_date: str | None = None
    thumbnail: str | None = None
    images: list[Any] | None = None
    tags: list[Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
