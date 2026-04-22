#!/usr/bin/env python3
"""
Script: contact.py
Demonstrates the Contact form API endpoint.

Usage:
    uv run scripts/contact.py

NOTE: This script sends a real HTTP request to the contact endpoint.
      Replace the placeholder values with genuine information before use.
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
        response = client.send_contact(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="0123456789",
            message="Hello, I would like to learn more about the open data portal.",
        )
        print_json("POST /api/v1/contact/", response)


if __name__ == "__main__":
    main()
