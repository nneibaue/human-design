#!/usr/bin/env python3
"""Test bodygraph endpoint with Nate's data."""

import requests
import json

response = requests.get(
    "http://localhost:8000/api/bodygraph",
    params={
        "date": "1992-08-13",
        "time": "09:13",
        "city": "Albuquerque",
        "country": "NM",
    }
)

print(f"Status: {response.status_code}")
print()

if response.status_code == 200:
    data = response.json()
    print(f"Type: {data['type']}")
    print(f"Authority: {data['authority']}")
    print(f"Profile: {data['profile']}")
    print(f"Defined Centers: {data['defined_centers']}")
    print(f"Active Channels: {data['active_channels']}")
    print()
    print(f"SVG length: {len(data['svg'])} characters")
    print(f"SVG starts with: {data['svg'][:100]}...")
else:
    print(f"Error: {response.text}")
