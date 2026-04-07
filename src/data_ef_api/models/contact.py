"""
Contact / Superset request-body models.

These are the only request bodies with fully defined schemas in the spec.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints


# Reusable stripped-string type (mirrors FastAPI's strip_whitespace=True)
_StrStripped = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class EmailRequest(BaseModel):
    """Request body for ``POST /api/v1/contact/``."""

    first_name: _StrStripped
    last_name: _StrStripped
    email: EmailStr
    phone: str = Field(min_length=9, max_length=15)
    message: _StrStripped


class DashboardTokenRequest(BaseModel):
    """Request body for ``POST /api/v1/superset/dashboard-token``."""

    dashboard_id: str
