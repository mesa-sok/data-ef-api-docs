#!/usr/bin/env python3
"""
Script: realtime_api.py
Demonstrates all Realtime API endpoints:
  - Khmer Riel Exchange Rate
  - Weather Forecast
  - Air Quality Index (AQI)
  - Ultraviolet Index (UV)
  - CSX Index
  - CSX Summary

Usage:
    uv run scripts/realtime_api.py
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
        # ── Exchange Rate ────────────────────────────────────────────
        print_json(
            "GET /api/v1/realtime-api/exchange-rate (all currencies)",
            client.get_exchange_rate(),
        )
        print_json(
            "GET /api/v1/realtime-api/exchange-rate?currency_id=USD",
            client.get_exchange_rate("USD"),
        )

        # ── Weather ──────────────────────────────────────────────────
        print_json(
            "GET /api/v1/realtime-api/weather (all provinces)",
            client.get_weather(),
        )
        print_json(
            "GET /api/v1/realtime-api/weather?province=Phnom Penh",
            client.get_weather("Phnom Penh"),
        )

        # ── Air Quality Index ────────────────────────────────────────
        print_json(
            "GET /api/v1/realtime-api/aqi (all provinces)",
            client.get_aqi(),
        )
        print_json(
            "GET /api/v1/realtime-api/aqi?province=Phnom Penh",
            client.get_aqi("Phnom Penh"),
        )

        # ── UV Index ─────────────────────────────────────────────────
        print_json(
            "GET /api/v1/realtime-api/uv (all provinces)",
            client.get_uv(),
        )
        print_json(
            "GET /api/v1/realtime-api/uv?province=Siem Reap",
            client.get_uv("Siem Reap"),
        )

        # ── CSX Index ────────────────────────────────────────────────
        print_json(
            "GET /api/v1/realtime-api/csx-index",
            client.get_csx_index(),
        )

        # ── CSX Summary ──────────────────────────────────────────────
        print_json(
            "GET /api/v1/realtime-api/csx-summary",
            client.get_csx_summary(),
        )


if __name__ == "__main__":
    main()
