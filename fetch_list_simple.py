#!/usr/bin/env python
"""Fetch the /list page - simple approach with direct session handling."""

import json
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# Use cached session cookies from working GateAPI
def load_cached_cookies():
    """Load cached cookies from GateAPI."""
    config_dir = Path.home() / ".config" / "human-design"
    cache_path = config_dir / "session.json"
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)
    return None

def fetch_list_page():
    """Fetch /list page using cached session."""

    BASE_URL = "https://www.64keys.com"

    session = requests.Session()

    # Try cached cookies first
    cached_cookies = load_cached_cookies()
    if cached_cookies:
        print("🍪 Using cached session cookies...")
        session.cookies.update(cached_cookies)

        # Test if session is still valid
        test = session.get(f"{BASE_URL}/list")
        if test.status_code == 200 and "/list" in test.url:
            print("✅ Cached session valid!\n")
        else:
            print("❌ Cached session expired, need to re-authenticate\n")
            cached_cookies = None

    # If no cached cookies or they're invalid, authenticate
    if not cached_cookies:
        print("🔐 Authenticating...")
        username = os.getenv("HD_USERNAME")
        password = os.getenv("HD_PASSWORD")

        if not username or not password:
            raise ValueError("HD_USERNAME and HD_PASSWORD must be set in .env")

        # Get CSRF tokens
        login_page = session.get(f"{BASE_URL}/login")
        soup = BeautifulSoup(login_page.text, "html.parser")

        # Get both CSRF token types
        csrf_meta = soup.find("meta", {"name": "csrf-token"})
        csrf_token = csrf_meta["content"] if csrf_meta else ""

        # Get the _token from the form
        token_input = soup.find("input", {"name": "_token"})
        form_token = token_input["value"] if token_input else csrf_token

        print(f"CSRF token: {csrf_token[:20]}...")
        print(f"Form token: {form_token[:20]}...")

        # Login with both tokens - don't follow redirects initially
        response = session.post(
            f"{BASE_URL}/login",
            data={
                "_token": form_token,
                "name": username,
                "password": password,
                "remember": "on"
            },
            headers={"X-CSRF-TOKEN": csrf_token},
            allow_redirects=False
        )

        print(f"Login POST response: {response.status_code}")
        print(f"Redirect location: {response.headers.get('Location', 'None')}")

        # Check if we got a redirect (successful login)
        if response.status_code in [301, 302, 303]:
            print("✅ Got redirect - following...")
            response = session.get(response.headers['Location'])
            print(f"After redirect: {response.url}")
        else:
            print(f"❌ No redirect - login may have failed")
            print(f"Response text preview: {response.text[:500]}")

    # Fetch /list page
    print("📄 Fetching /list page...")
    response = session.get(f"{BASE_URL}/list")

    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    print(f"Content length: {len(response.text)} bytes\n")

    # Save
    output_file = Path("64keys_list_page.html")
    with open(output_file, "w") as f:
        f.write(response.text)
    print(f"✅ Saved to: {output_file}\n")

    # Analyze
    soup = BeautifulSoup(response.text, "html.parser")

    print("🔍 Page analysis:")
    print(f"  Title: {soup.title.string if soup.title else 'N/A'}")

    tables = soup.find_all("table")
    print(f"  Tables: {len(tables)}")

    selects = soup.find_all("select")
    print(f"  Filter dropdowns: {len(selects)}")

    if selects:
        print("\n📋 Filters:")
        for select in selects[:10]:
            name = select.get("name", select.get("id", "unnamed"))
            options = select.find_all("option")
            print(f"    {name}: {len(options)} options")

    rows = soup.find_all("tr")
    if len(rows) > 1:
        print(f"\n📊 Data rows: {len(rows) - 1} (excluding header)")
        print("\nSample data:")
        for i, row in enumerate(rows[1:6], 1):
            cells = row.find_all(["td", "th"])
            if cells:
                data = " | ".join([c.get_text(strip=True) for c in cells])
                print(f"    {data[:200]}")

if __name__ == "__main__":
    try:
        fetch_list_page()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
