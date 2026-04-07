#!/usr/bin/env python3
"""
Script: events_news.py
Demonstrates the Events and News API endpoints.

Usage:
    uv run scripts/events_news.py
"""

import json
import sys

sys.path.insert(0, "src")

from data_ef_api import DataEFClient


def print_json(label: str, data: object) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print("=" * 60)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main() -> None:
    with DataEFClient() as client:
        # 1. List all events & news
        print_json(
            "GET /api/v1/events-and-news (events_and_news, page 1)",
            client.get_events_and_news(
                category="events_and_news",
                page=1,
                size=5,
                sort_by="created_at",
                order_by="desc",
            ),
        )

        # 2. List blog posts
        print_json(
            "GET /api/v1/events-and-news (blog, page 1)",
            client.get_events_and_news(category="blog", page=1, size=5),
        )

        # 3. Single item – fetch slug from the first result
        result = client.get_events_and_news(page=1, size=1)
        items = (
            result.get("data", {}).get("results", [])
            if isinstance(result, dict)
            else []
        )
        if items:
            slug = items[0].get("slug")
            if slug:
                print_json(
                    f"GET /api/v1/events-and-news/{slug}",
                    client.get_event_or_news(slug),
                )


if __name__ == "__main__":
    main()
