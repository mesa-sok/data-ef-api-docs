"""Error-response models for every realtime-API endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .enums import Error404Msg


# ── Exchange Rate ──────────────────────────────────────────────────────────────

class ExchangeRateError400(BaseModel):
    """400 response from the exchange-rate endpoint."""

    name: str = Field(default="ERROR_PARAMS")
    error_msg: str = Field(default="Invalid currency_id", alias="errorMsg")

    model_config = {"populate_by_name": True}


class ExchangeRateError404(BaseModel):
    """404 response from the exchange-rate endpoint."""

    name: str = Field(default="REAL_TIME_API_DATA_NOT_FOUND")
    error_msg: Error404Msg = Field(alias="errorMsg")

    model_config = {"populate_by_name": True}


# ── Weather ────────────────────────────────────────────────────────────────────

class WeatherError400(BaseModel):
    """400 response from the weather endpoint."""

    name: str = Field(default="ERROR_PARAMS")
    error_msg: str = Field(default="Invalid province", alias="errorMsg")

    model_config = {"populate_by_name": True}


class WeatherError404(BaseModel):
    """404 response from the weather endpoint."""

    name: str = Field(default="REAL_TIME_API_DATA_NOT_FOUND")
    error_msg: str = Field(default="Weather data not found", alias="errorMsg")

    model_config = {"populate_by_name": True}


# ── AQI ───────────────────────────────────────────────────────────────────────

class AqiError400(BaseModel):
    """400 response from the AQI endpoint."""

    name: str = Field(default="ERROR_PARAMS")
    error_msg: str = Field(default="Invalid province", alias="errorMsg")

    model_config = {"populate_by_name": True}


class AqiError404(BaseModel):
    """404 response from the AQI endpoint."""

    name: str = Field(default="REAL_TIME_API_DATA_NOT_FOUND")
    error_msg: str = Field(default="AQI data not found", alias="errorMsg")

    model_config = {"populate_by_name": True}


# ── UV ────────────────────────────────────────────────────────────────────────

class UvError400(BaseModel):
    """400 response from the UV endpoint."""

    name: str = Field(default="ERROR_PARAMS")
    error_msg: str = Field(default="Invalid province", alias="errorMsg")

    model_config = {"populate_by_name": True}


class UvError404(BaseModel):
    """404 response from the UV endpoint."""

    name: str = Field(default="REAL_TIME_API_DATA_NOT_FOUND")
    error_msg: str = Field(default="UV data not found", alias="errorMsg")

    model_config = {"populate_by_name": True}


# ── CSX Index ─────────────────────────────────────────────────────────────────

class CsxIndexError404(BaseModel):
    """404 response from the CSX-index endpoint."""

    name: str = Field(default="REAL_TIME_API_DATA_NOT_FOUND")
    error_msg: str = Field(default="CSX index data not found", alias="errorMsg")

    model_config = {"populate_by_name": True}


# ── CSX Summary ───────────────────────────────────────────────────────────────

class CsxSummaryError404(BaseModel):
    """404 response from the CSX-summary endpoint."""

    name: str = Field(default="REAL_TIME_API_DATA_NOT_FOUND")
    error_msg: str = Field(default="CSX summary data not found", alias="errorMsg")

    model_config = {"populate_by_name": True}
