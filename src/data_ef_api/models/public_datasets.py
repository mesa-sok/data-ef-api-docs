"""
Public-Datasets Pydantic models.

The OpenAPI spec does **not** define fixed response schemas for these
endpoints (all return ``{}``) so every model uses ``extra="allow"`` to
accept whatever the server sends.  Known fields are typed; anything
unexpected is silently kept.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ── Shared pagination wrapper ──────────────────────────────────────────────────

class DatasetListData(BaseModel):
    """Inner ``data`` object returned by the dataset-list endpoint."""

    model_config = {"extra": "allow"}

    results: list[Any] | None = None
    total: int | None = None
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None


class DatasetListResponse(BaseModel):
    """Response envelope for ``GET /api/v1/public-datasets``."""

    model_config = {"extra": "allow"}

    data: DatasetListData | None = None


# ── Home ──────────────────────────────────────────────────────────────────────

class HomeData(BaseModel):
    """Response for ``GET /api/v1/public-datasets/home``.

    Structure is not defined in the spec; all fields are optional.
    """

    model_config = {"extra": "allow"}

    featured_datasets: list[Any] | None = None
    recent_datasets: list[Any] | None = None
    stats: dict[str, Any] | None = None


# ── Count Data ────────────────────────────────────────────────────────────────

class CountData(BaseModel):
    """Response for ``GET /api/v1/public-datasets/count-data``."""

    model_config = {"extra": "allow"}

    datasets: int | None = None
    datasources: int | None = None


# ── Filter Options ────────────────────────────────────────────────────────────

class FilterOptionItem(BaseModel):
    """A single selectable option (category, organisation, format)."""

    model_config = {"extra": "allow"}

    id: str | int | None = None
    name: str | None = None
    slug: str | None = None
    count: int | None = None


class FilterOptions(BaseModel):
    """Response for ``GET /api/v1/public-datasets/filter-options``."""

    model_config = {"extra": "allow"}

    categories: list[FilterOptionItem] | None = None
    organizations: list[FilterOptionItem] | None = None
    data_formats: list[FilterOptionItem] | None = None


# ── Auto-suggest ──────────────────────────────────────────────────────────────

class AutoSuggestResponse(BaseModel):
    """Response for ``GET /api/v1/public-datasets/auto-suggest``."""

    model_config = {"extra": "allow"}

    suggestions: list[str | dict[str, Any]] | None = None


# ── SEO ───────────────────────────────────────────────────────────────────────

class SeoDataset(BaseModel):
    """One entry from ``GET /api/v1/public-datasets/seo``."""

    model_config = {"extra": "allow"}

    id: str | int | None = None
    slug: str | None = None
    title_en: str | None = None
    title_kh: str | None = None
    description_en: str | None = None
    description_kh: str | None = None


# ── Single Dataset Detail ──────────────────────────────────────────────────────

class DatasetDetail(BaseModel):
    """Response for ``GET /api/v1/public-datasets/{id}``.

    Many fields may be absent depending on the dataset type and locale.
    """

    model_config = {"extra": "allow"}

    id: str | int | None = None
    slug: str | None = None
    title_en: str | None = None
    title_kh: str | None = None
    description_en: str | None = None
    description_kh: str | None = None
    category: dict[str, Any] | None = None
    organization: dict[str, Any] | None = None
    tags: list[Any] | None = None
    license: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


# ── File Info ─────────────────────────────────────────────────────────────────

class DatasetFileEntry(BaseModel):
    """Metadata for a single downloadable file attached to a dataset."""

    model_config = {"extra": "allow"}

    id: str | int | None = None
    name: str | None = None
    format: str | None = None
    url: str | None = None
    size: int | str | None = None


class DatasetFileInfo(BaseModel):
    """Response for ``GET /api/v1/public-datasets/{id}/file``."""

    model_config = {"extra": "allow"}

    files: list[DatasetFileEntry] | None = None


# ── JSON Preview ──────────────────────────────────────────────────────────────

class DatasetJsonPreviewData(BaseModel):
    """Inner data wrapper for the JSON-preview endpoint."""

    model_config = {"extra": "allow"}

    results: list[dict[str, Any]] | None = None
    total: int | None = None
    page: int | None = None
    page_size: int | None = None


class DatasetJsonPreview(BaseModel):
    """Response for ``GET /api/v1/public-datasets/{id}/json``."""

    model_config = {"extra": "allow"}

    data: DatasetJsonPreviewData | None = None
    columns: list[str | dict[str, Any]] | None = None


# ── Map Data ──────────────────────────────────────────────────────────────────

class DatasetMapData(BaseModel):
    """Response for ``GET /api/v1/public-datasets/{id}/map-data``."""

    model_config = {"extra": "allow"}

    type: str | None = None
    features: list[dict[str, Any]] | None = None


# ── Realtime API Spec ─────────────────────────────────────────────────────────

class RealtimeApiSpec(BaseModel):
    """Response for ``GET /api/v1/public-datasets/{id}/realtime-api-spec``."""

    model_config = {"extra": "allow"}

    openapi: str | None = None
    info: dict[str, Any] | None = None
    paths: dict[str, Any] | None = None
