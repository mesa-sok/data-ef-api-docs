"""Enumerations used across the Data EF Public API."""

from enum import Enum


class SortByEnum(str, Enum):
    """Sort options for public-dataset listings."""

    MOST_RELEVANT = "MOST_RELEVANT"
    MOST_DOWNLOADED = "MOST_DOWNLOADED"
    RECENTLY_UPDATED = "RECENTLY_UPDATED"
    MOST_POPULAR = "MOST_POPULAR"
    NEWEST = "NEWEST"


class EventsAndNewsCategoryEnum(str, Enum):
    """Content category for events-and-news queries."""

    BLOG = "blog"
    EVENTS_AND_NEWS = "events_and_news"


class EventsAndNewsSortBy(str, Enum):
    """Field to sort events-and-news results by."""

    TITLE_EN = "title_en"
    TITLE_KH = "title_kh"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    EVENT_DATE = "event_date"


class EventsAndNewsOrderBy(str, Enum):
    """Sort direction for events-and-news results."""

    ASC = "asc"
    DESC = "desc"


class Error404Msg(str, Enum):
    """Possible 404 error messages for the exchange-rate endpoint."""

    NO_RATE_TODAY = "There is no today rate yet."
    NO_RATE_FOR_CURRENCY = "There is no today rate for this currency yet."
