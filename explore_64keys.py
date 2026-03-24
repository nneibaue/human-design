#!/usr/bin/env python
"""Explore 64keys.com to find saved charts/people.

Authenticates and scrapes available pages to discover saved data.
"""

import sys
from pathlib import Path

# Add src to path to import from api.py directly
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Import GateAPI directly from the file (not exported due to API refactor)
from human_design.api import GateAPI

load_dotenv()

def explore_64keys():
    """Explore 64keys.com structure."""

    api = GateAPI()

    print("🔐 Authenticating with 64keys.com...")
    api.authenticate()
    print("✅ Authenticated\n")

    # Explore main page
    print("📋 Exploring main page...")
    response = api.session.get(api.HOME_URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find navigation links
    print("\n🔗 Navigation links found:")
    nav_links = soup.find_all('a')

    for link in nav_links[:50]:  # First 50 links
        href = link.get('href', '')
        text = link.get_text(strip=True)

        if text and href and not href.startswith('#'):
            print(f"  {text}: {href}")

    # Try common URLs for saved charts
    print("\n\n🔍 Trying common chart/people URLs...")

    potential_urls = [
        "/charts",
        "/my-charts",
        "/people",
        "/my-people",
        "/saved",
        "/library",
        "/dashboard",
        "/profile",
    ]

    for path in potential_urls:
        url = f"{api.BASE_URL}{path}"
        try:
            response = api.session.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Found: {path}")

                # Check for data
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for charts or people listings
                charts = soup.find_all(['div', 'li', 'tr'], class_=lambda x: x and ('chart' in x.lower() or 'person' in x.lower()))
                if charts:
                    print(f"     Found {len(charts)} potential chart/person elements")
            elif response.status_code == 404:
                print(f"  ✗ Not found: {path}")
            else:
                print(f"  ? {path}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error on {path}: {e}")

    print("\n\n📄 Main page HTML structure (first 2000 chars):")
    print("="*60)
    print(soup.prettify()[:2000])
    print("="*60)

if __name__ == "__main__":
    explore_64keys()
