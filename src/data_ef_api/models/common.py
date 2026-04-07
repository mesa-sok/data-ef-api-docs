"""Shared / common Pydantic models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ValidationError(BaseModel):
    """A single validation-error entry returned by FastAPI on 422 responses."""

    loc: list[str | int]
    msg: str
    type: str


class HTTPValidationError(BaseModel):
    """Top-level 422 Validation Error response body."""

    detail: list[ValidationError] | None = None


class Pagination(BaseModel):
    """Generic pagination wrapper used by list endpoints.

    The API does not publish a fixed schema for the outer envelope of list
    responses, so all unknown fields are accepted (``extra="allow"``).
    """

    model_config = {"extra": "allow"}

    page: int | None = None
    page_size: int | None = None
    total: int | None = None
    total_pages: int | None = None
    results: list[Any] | None = None
