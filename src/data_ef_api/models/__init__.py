"""Pydantic models for the Data EF Public API."""

from .common import HTTPValidationError, Pagination, ValidationError
from .contact import DashboardTokenRequest, EmailRequest
from .enums import (
    Error404Msg,
    EventsAndNewsCategoryEnum,
    EventsAndNewsOrderBy,
    EventsAndNewsSortBy,
    SortByEnum,
)
from .errors import (
    AqiError400,
    AqiError404,
    CsxIndexError404,
    CsxSummaryError404,
    ExchangeRateError400,
    ExchangeRateError404,
    UvError400,
    UvError404,
    WeatherError400,
    WeatherError404,
)
from .events_news import EventsAndNewsDetail, EventsAndNewsList, EventsAndNewsListResponse
from .public_datasets import (
    CategoryOption,
    DataFormatOption,
    DatasetDetail,
    DatasetFileInfo,
    DatasetJsonPreview,
    DatasetListResponse,
    DatasetMapData,
    FilterOptions,
    HomeData,
    OrganizationOption,
    RealtimeApiSpec,
    SeoDataset,
)
from .realtime import (
    AqiResponse,
    CsxIndexResponse,
    CsxSummaryResponse,
    ExchangeRateResponse,
    SingleAqiResponse,
    SingleCsxIndexResponse,
    SingleCsxSummaryResponse,
    SingleExchangeRateResponse,
    SingleUvResponse,
    SingleWeatherResponse,
    UvResponse,
    WeatherResponse,
)

__all__ = [
    # common
    "HTTPValidationError",
    "Pagination",
    "ValidationError",
    # contact / superset
    "DashboardTokenRequest",
    "EmailRequest",
    # enums
    "Error404Msg",
    "EventsAndNewsCategoryEnum",
    "EventsAndNewsOrderBy",
    "EventsAndNewsSortBy",
    "SortByEnum",
    # error schemas
    "AqiError400",
    "AqiError404",
    "CsxIndexError404",
    "CsxSummaryError404",
    "ExchangeRateError400",
    "ExchangeRateError404",
    "UvError400",
    "UvError404",
    "WeatherError400",
    "WeatherError404",
    # events & news
    "EventsAndNewsDetail",
    "EventsAndNewsList",
    "EventsAndNewsListResponse",
    # public datasets
    "CategoryOption",
    "DataFormatOption",
    "DatasetDetail",
    "DatasetFileInfo",
    "DatasetJsonPreview",
    "DatasetListResponse",
    "DatasetMapData",
    "FilterOptions",
    "HomeData",
    "OrganizationOption",
    "RealtimeApiSpec",
    "SeoDataset",
    # realtime
    "AqiResponse",
    "CsxIndexResponse",
    "CsxSummaryResponse",
    "ExchangeRateResponse",
    "SingleAqiResponse",
    "SingleCsxIndexResponse",
    "SingleCsxSummaryResponse",
    "SingleExchangeRateResponse",
    "SingleUvResponse",
    "SingleWeatherResponse",
    "UvResponse",
    "WeatherResponse",
]
