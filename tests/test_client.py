"""Tests for DataEFClient using pytest-httpx."""

from __future__ import annotations

import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

import sys
sys.path.insert(0, "src")

from data_ef_api import DataEFClient
from data_ef_api.constants import BASE_URL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client() -> DataEFClient:
    return DataEFClient(base_url=BASE_URL)


# ---------------------------------------------------------------------------
# Public Datasets
# ---------------------------------------------------------------------------

class TestPublicDatasets:
    def test_get_home(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/home",
            json={"status": "ok"},
        )
        with _client() as c:
            data = c.get_home()
        assert data == {"status": "ok"}

    def test_get_count_data(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/count-data",
            json={"datasets": 100, "datasources": 200},
        )
        with _client() as c:
            data = c.get_count_data()
        assert data["datasets"] == 100

    def test_get_filter_options(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/filter-options",
            json={"categories": [], "organizations": [], "data_formats": []},
        )
        with _client() as c:
            data = c.get_filter_options()
        assert "categories" in data

    def test_get_auto_suggest_default(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/auto-suggest?keyword=",
            json={"suggestions": []},
        )
        with _client() as c:
            data = c.get_auto_suggest()
        assert "suggestions" in data

    def test_get_auto_suggest_with_keyword(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/auto-suggest?keyword=budget",
            json={"suggestions": ["budget 2024"]},
        )
        with _client() as c:
            data = c.get_auto_suggest("budget")
        assert data["suggestions"] == ["budget 2024"]

    def test_get_public_datasets_defaults(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="GET",
            url__startswith=f"{BASE_URL}/api/v1/public-datasets",
            json={"data": {"results": [], "total": 0}},
        )
        with _client() as c:
            data = c.get_public_datasets()
        assert "data" in data

    def test_get_public_datasets_seo(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/seo",
            json=[],
        )
        with _client() as c:
            data = c.get_public_datasets_seo()
        assert isinstance(data, list)

    def test_get_public_dataset(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123",
            json={"id": "abc-123", "title": "Test Dataset"},
        )
        with _client() as c:
            data = c.get_public_dataset("abc-123")
        assert data["id"] == "abc-123"

    def test_get_public_dataset_with_locale(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123?locale=km",
            json={"id": "abc-123"},
        )
        with _client() as c:
            data = c.get_public_dataset("abc-123", locale="km")
        assert data["id"] == "abc-123"

    def test_get_public_dataset_file(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123/file",
            json={"files": []},
        )
        with _client() as c:
            data = c.get_public_dataset_file("abc-123")
        assert "files" in data

    def test_get_public_dataset_json(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123/json?page=1&page_size=10",
            json={"data": []},
        )
        with _client() as c:
            data = c.get_public_dataset_json("abc-123")
        assert "data" in data

    def test_get_public_dataset_map_data(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123/map-data",
            json={"features": []},
        )
        with _client() as c:
            data = c.get_public_dataset_map_data("abc-123")
        assert "features" in data

    def test_get_realtime_api_spec(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/public-datasets/abc-123/realtime-api-spec",
            json={"openapi": "3.1.0"},
        )
        with _client() as c:
            data = c.get_realtime_api_spec("abc-123")
        assert data["openapi"] == "3.1.0"


# ---------------------------------------------------------------------------
# Events and News
# ---------------------------------------------------------------------------

class TestEventsAndNews:
    def test_get_events_and_news(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            method="GET",
            url__startswith=f"{BASE_URL}/api/v1/events-and-news",
            json={"data": {"results": [], "total": 0}},
        )
        with _client() as c:
            data = c.get_events_and_news()
        assert "data" in data

    def test_get_event_or_news(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/events-and-news/my-slug",
            json={"slug": "my-slug", "title_en": "Hello"},
        )
        with _client() as c:
            data = c.get_event_or_news("my-slug")
        assert data["slug"] == "my-slug"


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
    def test_send_contact(self, httpx_mock: HTTPXMock) -> None:
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
        assert "message" in data


# ---------------------------------------------------------------------------
# Realtime API
# ---------------------------------------------------------------------------

class TestRealtimeAPI:
    def test_get_exchange_rate_all(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/exchange-rate",
            json={"data": []},
        )
        with _client() as c:
            data = c.get_exchange_rate()
        assert "data" in data

    def test_get_exchange_rate_specific(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/exchange-rate?currency_id=USD",
            json={"data": {"currency_id": "USD"}},
        )
        with _client() as c:
            data = c.get_exchange_rate("USD")
        assert data["data"]["currency_id"] == "USD"

    def test_get_weather_all(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/weather",
            json={"data": []},
        )
        with _client() as c:
            data = c.get_weather()
        assert "data" in data

    def test_get_weather_province(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/weather?province=Phnom+Penh",
            json={"data": {"name": "Phnom Penh"}},
        )
        with _client() as c:
            data = c.get_weather("Phnom Penh")
        assert data["data"]["name"] == "Phnom Penh"

    def test_get_aqi_all(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/aqi",
            json={"data": []},
        )
        with _client() as c:
            data = c.get_aqi()
        assert "data" in data

    def test_get_aqi_province(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/aqi?province=Siem+Reap",
            json={"data": {"name": "Siem Reap"}},
        )
        with _client() as c:
            data = c.get_aqi("Siem Reap")
        assert data["data"]["name"] == "Siem Reap"

    def test_get_uv_all(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/uv",
            json={"data": []},
        )
        with _client() as c:
            data = c.get_uv()
        assert "data" in data

    def test_get_uv_province(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/uv?province=Battambang",
            json={"data": {"name": "Battambang"}},
        )
        with _client() as c:
            data = c.get_uv("Battambang")
        assert data["data"]["name"] == "Battambang"

    def test_get_csx_index(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/csx-index",
            json={"data": {"value": 742.5}},
        )
        with _client() as c:
            data = c.get_csx_index()
        assert data["data"]["value"] == 742.5

    def test_get_csx_summary(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/csx-summary",
            json={"data": []},
        )
        with _client() as c:
            data = c.get_csx_summary()
        assert "data" in data


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_http_error_raises(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/realtime-api/exchange-rate?currency_id=XXX",
            status_code=400,
            json={"name": "ERROR_PARAMS", "errorMsg": "Invalid currency_id"},
        )
        with _client() as c:
            with pytest.raises(httpx.HTTPStatusError):
                c.get_exchange_rate("XXX")

    def test_not_found_raises(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/events-and-news/nonexistent",
            status_code=404,
            json={"detail": "Not Found"},
        )
        with _client() as c:
            with pytest.raises(httpx.HTTPStatusError):
                c.get_event_or_news("nonexistent")
