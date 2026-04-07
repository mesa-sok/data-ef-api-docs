"""
Realtime-API Pydantic models.

These schemas are **fully defined** in the OpenAPI spec; only fields that the
spec marks as ``anyOf: [{type: X}, {type: null}]`` are typed ``X | None``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


# ── Exchange Rate ──────────────────────────────────────────────────────────────

class SingleExchangeRateResponse(BaseModel):
    """One currency's exchange-rate entry for today."""

    id: int
    valid_date: date
    created_at: datetime
    currency_id: str
    data: dict[str, Any]


class ExchangeRateResponse(BaseModel):
    """Response envelope for ``GET /api/v1/realtime-api/exchange-rate``.

    ``data`` is a single record when ``currency_id`` is provided, or a list
    when no filter is applied.
    """

    data: SingleExchangeRateResponse | list[SingleExchangeRateResponse]


# ── Weather ────────────────────────────────────────────────────────────────────

class SingleWeatherResponse(BaseModel):
    """Weather forecast for a single province."""

    id: int
    name: str
    created_at: datetime
    last_updated: datetime
    data: dict[str, Any]


class WeatherResponse(BaseModel):
    """Response envelope for ``GET /api/v1/realtime-api/weather``."""

    data: SingleWeatherResponse | list[SingleWeatherResponse]


# ── Air Quality Index ──────────────────────────────────────────────────────────

class SingleAqiResponse(BaseModel):
    """AQI reading for a single province."""

    id: int
    name: str
    created_at: datetime
    last_updated: datetime
    data: dict[str, Any]


class AqiResponse(BaseModel):
    """Response envelope for ``GET /api/v1/realtime-api/aqi``."""

    data: SingleAqiResponse | list[SingleAqiResponse]


# ── Ultraviolet Index ──────────────────────────────────────────────────────────

class SingleUvResponse(BaseModel):
    """UV index reading for a single province."""

    id: int
    name: str
    created_at: datetime
    last_updated: datetime
    data: dict[str, Any]


class UvResponse(BaseModel):
    """Response envelope for ``GET /api/v1/realtime-api/uv``."""

    data: SingleUvResponse | list[SingleUvResponse]


# ── CSX Index ─────────────────────────────────────────────────────────────────

class SingleCsxIndexResponse(BaseModel):
    """Cambodia Securities Exchange composite index snapshot.

    Only ``id`` and ``created_at`` are guaranteed; every other field may be
    absent (``null``) if trading data is not yet available.
    """

    id: int
    created_at: datetime
    date: str | None = None
    value: float | None = None
    change: float | None = None
    change_percent: float | None = None
    change_up_down: str | None = None
    index_time: str | None = None
    opening: float | None = None
    high: float | None = None
    low: float | None = None
    trading_volume: str | None = None
    trading_value: str | None = None
    market_cap: float | None = None


class CsxIndexResponse(BaseModel):
    """Response envelope for ``GET /api/v1/realtime-api/csx-index``."""

    data: SingleCsxIndexResponse


# ── CSX Summary ───────────────────────────────────────────────────────────────

class SingleCsxSummaryResponse(BaseModel):
    """Per-stock trading summary for a single CSX-listed company.

    Only ``id``, ``name``, and ``created_at`` are guaranteed; all other
    fields may be ``null`` when data is unavailable.
    """

    id: int
    name: str
    created_at: datetime
    icode: str | None = None
    dividend: float | None = None
    stock: str | None = None
    close: str | None = None
    change_up_down: str | None = None
    change: float | None = None
    open_price: str | None = None
    high: str | None = None
    low: str | None = None
    volume: str | None = None
    value: str | None = None
    pe: str | None = None
    pb: str | None = None


class CsxSummaryResponse(BaseModel):
    """Response envelope for ``GET /api/v1/realtime-api/csx-summary``."""

    data: list[SingleCsxSummaryResponse]
