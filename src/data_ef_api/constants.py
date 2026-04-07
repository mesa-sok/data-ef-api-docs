"""Constants for the Data EF Public API."""

BASE_URL = "https://data.mef.gov.kh"

SORT_BY_OPTIONS = [
    "MOST_RELEVANT",
    "MOST_DOWNLOADED",
    "RECENTLY_UPDATED",
    "MOST_POPULAR",
    "NEWEST",
]

CURRENCY_IDS = [
    "AUD", "CAD", "CHF", "CNH", "CNY", "EUR", "GBP", "HKD",
    "IDR", "INR", "JPY", "KRW", "LAK", "MMK", "MYR", "NZD",
    "PHP", "SDR", "SEK", "SGD", "THB", "TWD", "VND", "USD",
]

PROVINCES = [
    "Phnom Penh", "Sihanoukville", "Siem Reap", "Battambang",
    "Takeo", "Koh Kong", "Kratie", "Kampot", "Kep",
    "Kampong Thom", "Svay Rieng", "Mondulkiri", "Banteay Meanchey",
    "Kandal", "Prey Veng", "Kampong Chhnang", "Strung Treng",
    "Preah Vihear", "Tboung Khmum", "Pailin", "Ratanakiri",
    "Kampong Speu", "Kampong Cham", "Oddar Meanchey", "Pursat",
]

EVENTS_CATEGORIES = ["blog", "events_and_news"]

EVENTS_SORT_BY_OPTIONS = [
    "title_en", "title_kh", "created_at", "updated_at", "event_date",
]

EVENTS_ORDER_BY_OPTIONS = ["asc", "desc"]
