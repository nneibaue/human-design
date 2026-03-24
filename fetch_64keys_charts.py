#!/usr/bin/env python
"""Fetch saved charts from 64keys.com by logging in and scraping.

Direct implementation - doesn't rely on GateAPI class.
"""

import json
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

def get_credentials():
    """Get 64keys credentials from environment."""
    username = os.environ.get("HD_USERNAME")
    password = os.environ.get("HD_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Missing credentials. Set HD_USERNAME and HD_PASSWORD in .env"
        )

    return username, password


def login_to_64keys(session):
    """Authenticate with 64keys.com."""
    BASE_URL = "https://www.64keys.com"
    LOGIN_URL = f"{BASE_URL}/login"

    print("🔐 Logging in to 64keys.com...")

    # Get login page for CSRF token
    login_page = session.get(LOGIN_URL)
    soup = BeautifulSoup(login_page.text, "html.parser")
    csrf_token = soup.find("meta", {"name": "csrf-token"})["content"]

    # Login
    username, password = get_credentials()
    login_data = {"name": username, "password": password, "remember": "on"}
    response = session.post(
        LOGIN_URL,
        data=login_data,
        headers={"X-CSRF-TOKEN": csrf_token},
        allow_redirects=True,
    )

    print(f"Login response status: {response.status_code}")
    print(f"Final URL after redirects: {response.url}")

    # Try to access a protected page to verify login
    test_response = session.get(f"{BASE_URL}/list")
    if test_response.status_code == 200 and "list" not in test_response.url.lower():
        # We got redirected away from /list, probably to login
        raise Exception(f"Login verification failed - couldn't access /list. Check credentials.")

    print("✅ Logged in successfully\n")
    return session


def explore_64keys(session):
    """Explore 64keys.com to find where saved charts are."""
    BASE_URL = "https://www.64keys.com"

    print("🔍 Exploring 64keys.com structure...\n")

    # Check the /list page directly
    print("📄 Checking /list page (saved charts)...")
    list_response = session.get(f"{BASE_URL}/list")
    list_soup = BeautifulSoup(list_response.text, "html.parser")

    print(f"Status: {list_response.status_code}")
    print(f"URL: {list_response.url}")

    # Save the list page
    with open("64keys_list_page.html", "w") as f:
        f.write(list_response.text)
    print("✅ Saved to: 64keys_list_page.html")

    # Check main/home page
    print("\n📄 Checking main page...")
    response = session.get(f"{BASE_URL}/main")
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all navigation links
    print("\n🔗 Navigation links:")
    nav = soup.find('nav') or soup.find('div', {'class': 'nav'}) or soup.find('header')
    if nav:
        links = nav.find_all('a')
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if text and href:
                print(f"  - {text}: {href}")
    else:
        # Try all links
        all_links = soup.find_all('a')[:30]
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if text and href and not href.startswith('#') and not href.startswith('javascript'):
                print(f"  - {text}: {href}")

    # Try to find charts
    print("\n\n🔍 Looking for saved charts/people...")

    # Common URLs to try
    potential_urls = [
        "/charts",
        "/my-charts",
        "/people",
        "/my-people",
        "/saved",
        "/library",
        "/mycharts",
        "/mypeople",
        "/profile",
        "/user/charts",
    ]

    for path in potential_urls:
        url = f"{BASE_URL}{path}"
        try:
            response = session.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {path} - Found! (HTTP 200)")

                soup = BeautifulSoup(response.text, "html.parser")

                # Look for charts/people data
                # Try to find any elements that might contain chart data
                chart_elements = soup.find_all(['div', 'li', 'tr'], limit=20)
                data_found = False

                for elem in chart_elements:
                    text = elem.get_text(strip=True)
                    if len(text) > 10 and len(text) < 200:  # Reasonable text length
                        if any(keyword in text.lower() for keyword in ['chart', 'birth', 'date', 'time', 'person', 'name']):
                            if not data_found:
                                print(f"     Potential data found:")
                                data_found = True
                            print(f"       - {text[:100]}")

                if not data_found:
                    print(f"     No obvious chart data")

            elif response.status_code == 404:
                pass  # Silent for 404s
            else:
                print(f"? {path} - HTTP {response.status_code}")

        except Exception as e:
            pass  # Silent for errors

    # Check the actual main page now
    print("\n\n📄 Checking /main page (home)...")
    response = session.get(f"{BASE_URL}/main")
    soup = BeautifulSoup(response.text, "html.parser")

    # Save /library page for inspection
    print("\n💾 Checking /library page...")
    library_response = session.get(f"{BASE_URL}/library")
    library_soup = BeautifulSoup(library_response.text, "html.parser")

    # Save both pages
    with open("64keys_main_page.html", "w") as f:
        f.write(response.text)
    print("   Saved main page to: 64keys_main_page.html")

    with open("64keys_library_page.html", "w") as f:
        f.write(library_response.text)
    print("   Saved library page to: 64keys_library_page.html")

    # Look for forms or interactive elements that might list charts
    print("\n🔍 Looking for chart listing elements...")
    forms = soup.find_all('form')
    print(f"   Found {len(forms)} forms")

    tables = soup.find_all('table')
    print(f"   Found {len(tables)} tables")

    # Look for any divs with "chart" or "people" in class/id
    chart_divs = soup.find_all(['div', 'section'], class_=lambda x: x and ('chart' in str(x).lower() or 'people' in str(x).lower()))
    print(f"   Found {len(chart_divs)} divs with 'chart' or 'people' in class")

    # Print any promising divs
    for div in chart_divs[:5]:
        print(f"     - {div.get('class')}: {div.get_text(strip=True)[:100]}")


if __name__ == "__main__":
    session = requests.Session()

    try:
        login_to_64keys(session)
        explore_64keys(session)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
