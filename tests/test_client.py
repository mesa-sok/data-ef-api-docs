"""Tests for DataEFClient using pytest-httpx, asserting Pydantic model types."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

import sys
sys.path.insert(0, "src")

from data_ef_api import DataEFClient
from data_ef_api.constants import BASE_URL
from data_ef_api.models import (
    AqiResponse,
    CsxIndexResponse,
    CsxSummaryResponse,
    DatasetDetail,
    DatasetFileInfo,
    DatasetJsonPreview,
    DatasetListResponse,
    DatasetMapData,
    EventsAndNewsDetail,
    EventsAndNewsListResponse,
    ExchangeRateResponse,
    FilterOptions,
    HomeData,
    RealtimeApiSpec,
    UvResponse,
    WeatherResponse,
)
from data_ef_api.models.public_datasets import AutoSuggestResponse, CountData


def _client() -> DataEFClient:
    return DataEFClient(base_url=BASE_URL)


# ---------------------------------------------------------------------------
# Public Datasets
# ---------------------------------------------------------------------------

class TestPublicDatasets:
    def test_get_home_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/home",
            json={"featured_datasets": [], "stats": {"total": 50}},
        )
        with _client() as c:
            result = c.get_home()
        assert isinstance(result, HomeData)
        assert result.stats == {"total": 50}

    def test_get_home_extra_fields_allowed(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/home",
            json={"unknown_field": "value", "another": 123},
        )
        with _client() as c:
            result = c.get_home()
        assert isinstance(result, HomeData)

    def test_get_count_data_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/count-data",
            json={"datasets": 120, "datasources": 340},
        )
        with _client() as c:
            result = c.get_count_data()
        assert isinstance(result, CountData)
        assert result.datasets == 120
        assert result.datasources == 340

    def test_get_count_data_all_optional(self, httpx_mock: HTTPXMock) -> None:
        """Server may omit some count fields – model must still parse."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/count-data",
            json={},
        )
        with _client() as c:
            result = c.get_count_data()
        assert isinstance(result, CountData)
        assert result.datasets is None
        assert result.datasources is None

    def test_get_filter_options_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/filter-options",
            json={
                "categories": [{"id": 1, "name": "Finance", "slug": "finance"}],
                "organizations": [],
                "data_formats": [{"id": 2, "name": "CSV", "slug": "csv"}],
            },
        )
        with _client() as c:
            result = c.get_filter_options()
        assert isinstance(result, FilterOptions)
        assert result.categories[0].slug == "finance"

    def test_get_auto_suggest_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/auto-suggest?keyword=budget",
            json={"suggestions": ["budget 2024", "budget 2023"]},
        )
        with _client() as c:
            result = c.get_auto_suggest("budget")
        assert isinstance(result, AutoSuggestResponse)
        assert "budget 2024" in result.suggestions

    def test_get_auto_suggest_empty_keyword(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/auto-suggest?keyword=",
            json={"suggestions": []},
        )
        with _client() as c:
            result = c.get_auto_suggest()
        assert isinstance(result, AutoSuggestResponse)
        assert result.suggestions == []

    def test_get_public_datasets_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets?keyword=budget&sort_by=MOST_RELEVANT&page=1&page_size=20",
            json={
                "data": {
                    "results": [{"id": "ds-1", "title_en": "Budget 2024"}],
                    "total": 1,
                    "page": 1,
                    "page_size": 20,
                }
            },
        )
        with _client() as c:
            result = c.get_public_datasets(keyword="budget")
        assert isinstance(result, DatasetListResponse)
        assert result.data.total == 1

    def test_get_public_datasets_empty_result(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets?sort_by=MOST_RELEVANT&page=1&page_size=20",
            json={"data": {"results": [], "total": 0}},
        )
        with _client() as c:
            result = c.get_public_datasets()
        assert isinstance(result, DatasetListResponse)
        assert result.data.results == []

    def test_get_public_dataset_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123",
            json={
                "id": "abc-123",
                "slug": "abc-123",
                "title_en": "Test Dataset",
                "title_kh": "ទិន្នន័យសាកល្បង",
            },
        )
        with _client() as c:
            result = c.get_public_dataset("abc-123")
        assert isinstance(result, DatasetDetail)
        assert result.id == "abc-123"
        assert result.title_en == "Test Dataset"

    def test_get_public_dataset_optional_fields_absent(self, httpx_mock: HTTPXMock) -> None:
        """Many optional fields may be missing from the server response."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/min-dataset",
            json={"id": "min-dataset"},
        )
        with _client() as c:
            result = c.get_public_dataset("min-dataset")
        assert isinstance(result, DatasetDetail)
        assert result.category is None
        assert result.organization is None
        assert result.tags is None

    def test_get_public_dataset_with_locale(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123?locale=km",
            json={"id": "abc-123", "title_kh": "ទិន្នន័យ"},
        )
        with _client() as c:
            result = c.get_public_dataset("abc-123", locale="km")
        assert isinstance(result, DatasetDetail)
        assert result.title_kh == "ទិន្នន័យ"

    def test_get_public_dataset_file_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123/file",
            json={"files": [{"id": 1, "name": "data.csv", "format": "CSV", "url": "https://example.com/data.csv"}]},
        )
        with _client() as c:
            result = c.get_public_dataset_file("abc-123")
        assert isinstance(result, DatasetFileInfo)
        assert result.files[0].format == "CSV"

    def test_get_public_dataset_file_no_files(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123/file",
            json={},
        )
        with _client() as c:
            result = c.get_public_dataset_file("abc-123")
        assert isinstance(result, DatasetFileInfo)
        assert result.files is None

    def test_get_public_dataset_json_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123/json?page=1&page_size=10",
            json={
                "data": {"results": [{"year": 2024, "value": 100}], "total": 1},
                "columns": ["year", "value"],
            },
        )
        with _client() as c:
            result = c.get_public_dataset_json("abc-123")
        assert isinstance(result, DatasetJsonPreview)
        assert result.columns == ["year", "value"]

    def test_get_public_dataset_map_data_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123/map-data",
            json={"type": "FeatureCollection", "features": []},
        )
        with _client() as c:
            result = c.get_public_dataset_map_data("abc-123")
        assert isinstance(result, DatasetMapData)
        assert result.type == "FeatureCollection"

    def test_get_realtime_api_spec_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123/realtime-api-spec",
            json={"openapi": "3.1.0", "info": {"title": "Dataset API"}, "paths": {}},
        )
        with _client() as c:
            result = c.get_realtime_api_spec("abc-123")
        assert isinstance(result, RealtimeApiSpec)
        assert result.openapi == "3.1.0"


# ---------------------------------------------------------------------------
# Events and News
# ---------------------------------------------------------------------------

class TestEventsAndNews:
    def test_get_events_list_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/events-and-news?category=events_and_news&page=1&size=10",
            json={
                "data": {
                    "results": [
                        {
                            "id": 1,
                            "slug": "event-1",
                            "title_en": "Annual Conference 2024",
                            "category": "events_and_news",
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "size": 10,
                }
            },
        )
        with _client() as c:
            result = c.get_events_and_news(category="events_and_news")
        assert isinstance(result, EventsAndNewsListResponse)
        assert result.data.results[0].slug == "event-1"

    def test_get_events_list_optional_fields(self, httpx_mock: HTTPXMock) -> None:
        """event_date, thumbnail etc. may be absent."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/events-and-news?category=blog&page=1&size=10",
            json={"data": {"results": [{"id": 1, "slug": "blog-1"}], "total": 1}},
        )
        with _client() as c:
            result = c.get_events_and_news(category="blog")
        assert isinstance(result, EventsAndNewsListResponse)
        assert result.data.results[0].event_date is None
        assert result.data.results[0].thumbnail is None

    def test_get_event_detail_returns_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/events-and-news/my-slug",
            json={
                "id": 5,
                "slug": "my-slug",
                "title_en": "Hello World",
                "body_en": "<p>Content</p>",
                "category": "blog",
            },
        )
        with _client() as c:
            result = c.get_event_or_news("my-slug")
        assert isinstance(result, EventsAndNewsDetail)
        assert result.slug == "my-slug"
        assert result.body_kh is None  # not provided – optional


# ---------------------------------------------------------------------------
# Superset
# ---------------------------------------------------------------------------

class TestSuperset:
    def test_get_dashboard_token(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/superset/dashboard-token",
            method="POST",
            json={"token": "abc.def.ghi"},
        )
        with _client() as c:
            data = c.get_dashboard_token("dashboard-uuid")
        assert data["token"] == "abc.def.ghi"


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

class TestContact:
    def test_send_contact_success(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/contact/",
            method="POST",
            json={"message": "Email sent successfully"},
        )
        with _client() as c:
            data = c.send_contact(
                first_name="Jane",
                last_name="Doe",
                email="jane@example.com",
                phone="0123456789",
                message="Hello",
            )
        assert data["message"] == "Email sent successfully"


# ---------------------------------------------------------------------------
# Realtime – Exchange Rate
# ---------------------------------------------------------------------------

class TestExchangeRate:
    def test_get_all_currencies_returns_list_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/exchange-rate",
            json={
                "data": [
                    {
                        "id": 1,
                        "valid_date": "2024-01-15",
                        "created_at": "2024-01-15T08:00:00",
                        "currency_id": "USD",
                        "data": {"buy": 4050.0, "sell": 4060.0},
                    }
                ]
            },
        )
        with _client() as c:
            result = c.get_exchange_rate()
        assert isinstance(result, ExchangeRateResponse)
        assert isinstance(result.data, list)
        assert result.data[0].currency_id == "USD"

    def test_get_single_currency_returns_single_model(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/exchange-rate?currency_id=USD",
            json={
                "data": {
                    "id": 1,
                    "valid_date": "2024-01-15",
                    "created_at": "2024-01-15T08:00:00",
                    "currency_id": "USD",
                    "data": {"buy": 4050.0, "sell": 4060.0},
                }
            },
        )
        with _client() as c:
            result = c.get_exchange_rate("USD")
        assert isinstance(result, ExchangeRateResponse)
        # single record → not a list
        assert not isinstance(result.data, list)
        assert result.data.currency_id == "USD"


# ---------------------------------------------------------------------------
# Realtime – Weather
# ---------------------------------------------------------------------------

class TestWeather:
    def test_get_all_provinces_returns_list(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/weather",
            json={
                "data": [
                    {
                        "id": 1,
                        "name": "Phnom Penh",
                        "created_at": "2024-01-15T08:00:00",
                        "last_updated": "2024-01-15T07:00:00",
                        "data": {"temp_c": 30.5, "condition": "Sunny"},
                    }
                ]
            },
        )
        with _client() as c:
            result = c.get_weather()
        assert isinstance(result, WeatherResponse)
        assert isinstance(result.data, list)
        assert result.data[0].name == "Phnom Penh"

    def test_get_single_province(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/weather?province=Phnom+Penh",
            json={
                "data": {
                    "id": 1,
                    "name": "Phnom Penh",
                    "created_at": "2024-01-15T08:00:00",
                    "last_updated": "2024-01-15T07:00:00",
                    "data": {"temp_c": 30.5},
                }
            },
        )
        with _client() as c:
            result = c.get_weather("Phnom Penh")
        assert isinstance(result, WeatherResponse)
        assert not isinstance(result.data, list)
        assert result.data.name == "Phnom Penh"


# ---------------------------------------------------------------------------
# Realtime – AQI
# ---------------------------------------------------------------------------

class TestAqi:
    def test_get_all_provinces(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/aqi",
            json={
                "data": [
                    {
                        "id": 1,
                        "name": "Phnom Penh",
                        "created_at": "2024-01-15T08:00:00",
                        "last_updated": "2024-01-15T07:30:00",
                        "data": {"aqi": 42, "category": "Good"},
                    }
                ]
            },
        )
        with _client() as c:
            result = c.get_aqi()
        assert isinstance(result, AqiResponse)
        assert isinstance(result.data, list)
        assert result.data[0].data["aqi"] == 42

    def test_get_single_province(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/aqi?province=Siem+Reap",
            json={
                "data": {
                    "id": 2,
                    "name": "Siem Reap",
                    "created_at": "2024-01-15T08:00:00",
                    "last_updated": "2024-01-15T07:30:00",
                    "data": {"aqi": 35},
                }
            },
        )
        with _client() as c:
            result = c.get_aqi("Siem Reap")
        assert isinstance(result, AqiResponse)
        assert not isinstance(result.data, list)
        assert result.data.name == "Siem Reap"


# ---------------------------------------------------------------------------
# Realtime – UV
# ---------------------------------------------------------------------------

class TestUv:
    def test_get_all_provinces(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/uv",
            json={
                "data": [
                    {
                        "id": 1,
                        "name": "Battambang",
                        "created_at": "2024-01-15T09:00:00",
                        "last_updated": "2024-01-15T08:00:00",
                        "data": {"uv_index": 8, "level": "Very High"},
                    }
                ]
            },
        )
        with _client() as c:
            result = c.get_uv()
        assert isinstance(result, UvResponse)
        assert isinstance(result.data, list)

    def test_get_single_province(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/uv?province=Battambang",
            json={
                "data": {
                    "id": 1,
                    "name": "Battambang",
                    "created_at": "2024-01-15T09:00:00",
                    "last_updated": "2024-01-15T08:00:00",
                    "data": {"uv_index": 8},
                }
            },
        )
        with _client() as c:
            result = c.get_uv("Battambang")
        assert isinstance(result, UvResponse)
        assert not isinstance(result.data, list)
        assert result.data.name == "Battambang"


# ---------------------------------------------------------------------------
# Realtime – CSX Index (many optional fields)
# ---------------------------------------------------------------------------

class TestCsxIndex:
    def test_get_csx_index_full(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/csx-index",
            json={
                "data": {
                    "id": 1,
                    "created_at": "2024-01-15T10:00:00",
                    "date": "2024-01-15",
                    "value": 742.5,
                    "change": 3.2,
                    "change_percent": 0.43,
                    "change_up_down": "up",
                    "index_time": "10:00",
                    "opening": 739.3,
                    "high": 745.0,
                    "low": 738.1,
                    "trading_volume": "1,200,000",
                    "trading_value": "4,560,000,000",
                    "market_cap": 12500000000.0,
                }
            },
        )
        with _client() as c:
            result = c.get_csx_index()
        assert isinstance(result, CsxIndexResponse)
        assert result.data.value == 742.5
        assert result.data.change_up_down == "up"

    def test_get_csx_index_minimal(self, httpx_mock: HTTPXMock) -> None:
        """Only id + created_at are guaranteed by the spec."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/csx-index",
            json={"data": {"id": 1, "created_at": "2024-01-15T10:00:00"}},
        )
        with _client() as c:
            result = c.get_csx_index()
        assert isinstance(result, CsxIndexResponse)
        assert result.data.value is None
        assert result.data.change is None
        assert result.data.market_cap is None


# ---------------------------------------------------------------------------
# Realtime – CSX Summary (many optional fields)
# ---------------------------------------------------------------------------

class TestCsxSummary:
    def test_get_csx_summary_full(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/csx-summary",
            json={
                "data": [
                    {
                        "id": 1,
                        "name": "ACLEDA Bank",
                        "created_at": "2024-01-15T10:00:00",
                        "icode": "ACB",
                        "dividend": 0.5,
                        "stock": "ACB",
                        "close": "8,500",
                        "change_up_down": "up",
                        "change": 100.0,
                        "open_price": "8,400",
                        "high": "8,600",
                        "low": "8,380",
                        "volume": "25,000",
                        "value": "212,500,000",
                        "pe": "12.5",
                        "pb": "1.8",
                    }
                ]
            },
        )
        with _client() as c:
            result = c.get_csx_summary()
        assert isinstance(result, CsxSummaryResponse)
        assert len(result.data) == 1
        assert result.data[0].name == "ACLEDA Bank"
        assert result.data[0].icode == "ACB"

    def test_get_csx_summary_minimal(self, httpx_mock: HTTPXMock) -> None:
        """id, name, created_at required; everything else may be null."""
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/csx-summary",
            json={
                "data": [{"id": 1, "name": "Some Corp", "created_at": "2024-01-15T10:00:00"}]
            },
        )
        with _client() as c:
            result = c.get_csx_summary()
        assert isinstance(result, CsxSummaryResponse)
        assert result.data[0].icode is None
        assert result.data[0].dividend is None
        assert result.data[0].pe is None

    def test_get_csx_summary_empty_list(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/csx-summary",
            json={"data": []},
        )
        with _client() as c:
            result = c.get_csx_summary()
        assert isinstance(result, CsxSummaryResponse)
        assert result.data == []


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_exchange_rate_400_raises_http_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/exchange-rate?currency_id=XXX",
            status_code=400,
            json={"name": "ERROR_PARAMS", "errorMsg": "Invalid currency_id"},
        )
        with _client() as c:
            with pytest.raises(httpx.HTTPStatusError):
                c.get_exchange_rate("XXX")

    def test_event_not_found_raises_http_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/events-and-news/nonexistent-slug",
            status_code=404,
            json={"detail": "Not Found"},
        )
        with _client() as c:
            with pytest.raises(httpx.HTTPStatusError):
                c.get_event_or_news("nonexistent-slug")

    def test_aqi_invalid_province_raises(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/aqi?province=Nowhere",
            status_code=400,
            json={"name": "ERROR_PARAMS", "errorMsg": "Invalid province"},
        )
        with _client() as c:
            with pytest.raises(httpx.HTTPStatusError):
                c.get_aqi("Nowhere")
