"""HTTP client for the Data EF Public API (https://data.mef.gov.kh/api/v1/...)."""

from __future__ import annotations

from typing import Any

import httpx

from .constants import BASE_URL
from .models.events_news import EventsAndNewsDetail, EventsAndNewsListResponse
from .models.public_datasets import (
    AutoSuggestResponse,
    CountData,
    DatasetDetail,
    DatasetFileInfo,
    DatasetJsonPreview,
    DatasetListResponse,
    DatasetMapData,
    FilterOptions,
    HomeData,
    RealtimeApiSpec,
)
from .models.realtime import (
    AqiResponse,
    CsxIndexResponse,
    CsxSummaryResponse,
    ExchangeRateResponse,
    UvResponse,
    WeatherResponse,
)


class DataEFClient:
    """Synchronous client for the Data EF Public API.

    Args:
        base_url: Root URL of the API. Defaults to ``https://data.mef.gov.kh``.
        timeout: Request timeout in seconds. Defaults to ``30``.
        verify: Verify SSL certificates. Defaults to ``True``.

    Example::

        from data_ef_api import DataEFClient

        with DataEFClient() as client:
            home = client.get_home()
            print(home.model_dump())
    """

    def __init__(self, base_url: str = BASE_URL, timeout: float = 30.0, verify: bool = True) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout, verify=verify)

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "DataEFClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform a GET request and return the parsed JSON body."""
        response = self._client.get(path, params=self._clean(params))
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Perform a POST request and return the parsed JSON body."""
        response = self._client.post(path, json=json)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _clean(params: dict[str, Any] | None) -> dict[str, Any] | None:
        """Remove *None* values from query-parameter dictionaries."""
        if params is None:
            return None
        return {k: v for k, v in params.items() if v is not None}

    # ==================================================================
    # Public Datasets
    # ==================================================================

    def get_home(self) -> HomeData:
        """Return homepage summary data.

        ``GET /api/v1/public-datasets/home``
        """
        return HomeData.model_validate(self._get("/api/v1/public-datasets/home"))

    def get_count_data(self) -> CountData:
        """Return total counts of datasets and data-sources.

        ``GET /api/v1/public-datasets/count-data``
        """
        return CountData.model_validate(self._get("/api/v1/public-datasets/count-data"))

    def get_filter_options(self) -> FilterOptions:
        """Return available filter options (categories, organisations, formats).

        ``GET /api/v1/public-datasets/filter-options``
        """
        return FilterOptions.model_validate(
            self._get("/api/v1/public-datasets/filter-options")
        )

    def get_auto_suggest(self, keyword: str = "") -> AutoSuggestResponse:
        """Return search auto-suggestions for the given *keyword*.

        ``GET /api/v1/public-datasets/auto-suggest``

        Args:
            keyword: Partial search term. Defaults to ``""``.
        """
        return AutoSuggestResponse.model_validate(
            self._get("/api/v1/public-datasets/auto-suggest", {"keyword": keyword})
        )

    def get_public_datasets(
        self,
        *,
        keyword: str | None = None,
        categories: str | None = None,
        organizations: str | None = None,
        data_formats: str | None = None,
        sort_by: str | None = "MOST_RELEVANT",
        page: int = 1,
        page_size: int = 20,
    ) -> DatasetListResponse:
        """Search and list public datasets.

        ``GET /api/v1/public-datasets``

        Args:
            keyword: Free-text search term.
            categories: Comma-separated category slugs to filter by.
            organizations: Comma-separated organisation slugs to filter by.
            data_formats: Comma-separated format names to filter by
                (e.g. ``"CSV,JSON"``).
            sort_by: One of ``MOST_RELEVANT``, ``MOST_DOWNLOADED``,
                ``RECENTLY_UPDATED``, ``MOST_POPULAR``, ``NEWEST``.
                Defaults to ``MOST_RELEVANT``.
            page: 1-based page number. Defaults to ``1``.
            page_size: Items per page (0–10 000). Defaults to ``20``.
        """
        return DatasetListResponse.model_validate(
            self._get(
                "/api/v1/public-datasets",
                {
                    "keyword": keyword,
                    "categories": categories,
                    "organizations": organizations,
                    "data_formats": data_formats,
                    "sort_by": sort_by,
                    "page": page,
                    "page_size": page_size,
                },
            )
        )

    def get_public_datasets_seo(self) -> list[Any]:
        """Return SEO metadata for all public datasets.

        ``GET /api/v1/public-datasets/seo``
        """
        return self._get("/api/v1/public-datasets/seo")

    def get_public_dataset(
        self, dataset_id: str, locale: str | None = None
    ) -> DatasetDetail:
        """Return detail for a single dataset.

        ``GET /api/v1/public-datasets/{id}``

        Args:
            dataset_id: Dataset identifier (slug or UUID).
            locale: Language code, e.g. ``"en"`` or ``"km"``.
        """
        return DatasetDetail.model_validate(
            self._get(
                f"/api/v1/public-datasets/{dataset_id}",
                {"locale": locale},
            )
        )

    def get_public_dataset_file(self, dataset_id: str) -> DatasetFileInfo:
        """Return file metadata (download links) for a dataset.

        ``GET /api/v1/public-datasets/{id}/file``

        Args:
            dataset_id: Dataset identifier.
        """
        return DatasetFileInfo.model_validate(
            self._get(f"/api/v1/public-datasets/{dataset_id}/file")
        )

    def get_public_dataset_json(
        self,
        dataset_id: str,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> DatasetJsonPreview:
        """Return a paginated JSON preview of a dataset's contents.

        ``GET /api/v1/public-datasets/{id}/json``

        Args:
            dataset_id: Dataset identifier.
            page: 1-based page number. Defaults to ``1``.
            page_size: Items per page (0–200). Defaults to ``10``.
        """
        return DatasetJsonPreview.model_validate(
            self._get(
                f"/api/v1/public-datasets/{dataset_id}/json",
                {"page": page, "page_size": page_size},
            )
        )

    def get_public_dataset_map_data(self, dataset_id: str) -> DatasetMapData:
        """Return geographic/map data for a dataset.

        ``GET /api/v1/public-datasets/{id}/map-data``

        Args:
            dataset_id: Dataset identifier.
        """
        return DatasetMapData.model_validate(
            self._get(f"/api/v1/public-datasets/{dataset_id}/map-data")
        )

    def get_realtime_api_spec(self, dataset_id: str) -> RealtimeApiSpec:
        """Return the real-time API specification for a dataset.

        ``GET /api/v1/public-datasets/{id}/realtime-api-spec``

        Args:
            dataset_id: Dataset identifier.
        """
        return RealtimeApiSpec.model_validate(
            self._get(f"/api/v1/public-datasets/{dataset_id}/realtime-api-spec")
        )

    # ==================================================================
    # Events and News
    # ==================================================================

    def get_events_and_news(
        self,
        *,
        category: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        size: int = 10,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> EventsAndNewsListResponse:
        """List events and news (or blog) articles.

        ``GET /api/v1/events-and-news``

        Args:
            category: ``"blog"`` or ``"events_and_news"``.
            keyword: Free-text search term.
            page: Page number. Defaults to ``1``.
            size: Items per page. Defaults to ``10``.
            sort_by: One of ``title_en``, ``title_kh``, ``created_at``,
                ``updated_at``, ``event_date``.
            order_by: ``"asc"`` or ``"desc"``.
        """
        return EventsAndNewsListResponse.model_validate(
            self._get(
                "/api/v1/events-and-news",
                {
                    "category": category,
                    "keyword": keyword,
                    "page": page,
                    "size": size,
                    "sort_by": sort_by,
                    "order_by": order_by,
                },
            )
        )

    def get_event_or_news(self, slug: str) -> EventsAndNewsDetail:
        """Return a single event / news article by its slug.

        ``GET /api/v1/events-and-news/{events_and_news_slug}``

        Args:
            slug: URL slug of the article.
        """
        return EventsAndNewsDetail.model_validate(
            self._get(f"/api/v1/events-and-news/{slug}")
        )

    # ==================================================================
    # Superset
    # ==================================================================

    def get_dashboard_token(self, dashboard_id: str) -> dict[str, Any]:
        """Request a guest token for an embedded Superset dashboard.

        ``POST /api/v1/superset/dashboard-token``

        Args:
            dashboard_id: Superset dashboard UUID or identifier.
        """
        return self._post(
            "/api/v1/superset/dashboard-token",
            {"dashboard_id": dashboard_id},
        )

    # ==================================================================
    # Contact
    # ==================================================================

    def send_contact(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        message: str,
    ) -> dict[str, Any]:
        """Submit a contact / enquiry form.

        ``POST /api/v1/contact/``

        Args:
            first_name: Sender's first name (required, non-empty).
            last_name: Sender's last name (required, non-empty).
            email: Sender's email address.
            phone: Sender's phone number (9–15 digits).
            message: Message body (required, non-empty).
        """
        return self._post(
            "/api/v1/contact/",
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "message": message,
            },
        )

    # ==================================================================
    # Realtime API – Exchange Rate
    # ==================================================================

    def get_exchange_rate(
        self, currency_id: str | None = None
    ) -> ExchangeRateResponse:
        """Return today's KHR exchange rate(s) from the National Bank of Cambodia.

        ``GET /api/v1/realtime-api/exchange-rate``

        Args:
            currency_id: ISO currency code, e.g. ``"USD"``.
                If omitted, all currencies are returned.
        """
        return ExchangeRateResponse.model_validate(
            self._get(
                "/api/v1/realtime-api/exchange-rate",
                {"currency_id": currency_id},
            )
        )

    # ==================================================================
    # Realtime API – Weather
    # ==================================================================

    def get_weather(self, province: str | None = None) -> WeatherResponse:
        """Return the latest weather forecast for Cambodia.

        ``GET /api/v1/realtime-api/weather``

        Args:
            province: Province name, e.g. ``"Phnom Penh"``.
                If omitted, all provinces are returned.
        """
        return WeatherResponse.model_validate(
            self._get("/api/v1/realtime-api/weather", {"province": province})
        )

    # ==================================================================
    # Realtime API – Air Quality Index
    # ==================================================================

    def get_aqi(self, province: str | None = None) -> AqiResponse:
        """Return the latest Air Quality Index (AQI) for Cambodia.

        ``GET /api/v1/realtime-api/aqi``

        Args:
            province: Province name, e.g. ``"Phnom Penh"``.
                If omitted, all provinces are returned.
        """
        return AqiResponse.model_validate(
            self._get("/api/v1/realtime-api/aqi", {"province": province})
        )

    # ==================================================================
    # Realtime API – UV Index
    # ==================================================================

    def get_uv(self, province: str | None = None) -> UvResponse:
        """Return the latest Ultraviolet (UV) Index for Cambodia.

        ``GET /api/v1/realtime-api/uv``

        Args:
            province: Province name, e.g. ``"Phnom Penh"``.
                If omitted, all provinces are returned.
        """
        return UvResponse.model_validate(
            self._get("/api/v1/realtime-api/uv", {"province": province})
        )

    # ==================================================================
    # Realtime API – CSX Index
    # ==================================================================

    def get_csx_index(self) -> CsxIndexResponse:
        """Return the latest Cambodia Securities Exchange (CSX) index.

        ``GET /api/v1/realtime-api/csx-index``
        """
        return CsxIndexResponse.model_validate(
            self._get("/api/v1/realtime-api/csx-index")
        )

    # ==================================================================
    # Realtime API – CSX Summary
    # ==================================================================

    def get_csx_summary(self) -> CsxSummaryResponse:
        """Return the latest Cambodia Securities Exchange (CSX) trading summary.

        ``GET /api/v1/realtime-api/csx-summary``
        """
        return CsxSummaryResponse.model_validate(
            self._get("/api/v1/realtime-api/csx-summary")
        )
