#!/usr/bin/env python
"""Fetch the /list page using the working GateAPI class."""

import sys
from pathlib import Path

# Import directly from api.py module
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the module, then get GateAPI from it
import importlib.util
spec = importlib.util.spec_from_file_location("hd_api", "src/human_design/api.py")
hd_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hd_api)

GateAPI = hd_api.GateAPI

from bs4 import BeautifulSoup

def fetch_list_page():
    """Fetch the /list page with saved charts."""

    print("🔐 Authenticating with 64keys.com...")
    api = GateAPI()
    api.authenticate()
    print("✅ Authenticated\n")

    # Fetch /list page
    print("📄 Fetching /list page...")
    list_url = f"{api.BASE_URL}/list"
    response = api.session.get(list_url)

    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    print(f"Content length: {len(response.text)} bytes")

    # Save the page
    output_file = Path("64keys_list_page.html")
    with open(output_file, "w") as f:
        f.write(response.text)
    print(f"✅ Saved to: {output_file}\n")

    # Parse and examine structure
    soup = BeautifulSoup(response.text, "html.parser")

    print("🔍 Page analysis:")
    print(f"  Title: {soup.title.string if soup.title else 'N/A'}")

    # Look for tables
    tables = soup.find_all("table")
    print(f"  Tables found: {len(tables)}")

    # Look for forms/filters
    forms = soup.find_all("form")
    print(f"  Forms found: {len(forms)}")

    # Look for select elements (filters)
    selects = soup.find_all("select")
    print(f"  Select dropdowns found: {len(selects)}")

    if selects:
        print("\n📋 Filter options found:")
        for select in selects[:5]:  # First 5
            name = select.get("name", "unnamed")
            options = [opt.get_text(strip=True) for opt in select.find_all("option")]
            print(f"    {name}: {len(options)} options")
            if len(options) <= 10:
                print(f"      Options: {', '.join(options)}")

    # Look for any rows that might contain chart data
    rows = soup.find_all("tr")
    print(f"\n  Table rows found: {len(rows)}")

    if len(rows) > 1:
        print("\n📊 Sample row data (first few rows):")
        for i, row in enumerate(rows[1:6], 1):  # Skip header, show first 5
            cells = row.find_all(["td", "th"])
            if cells:
                row_text = " | ".join([cell.get_text(strip=True) for cell in cells])
                print(f"    Row {i}: {row_text[:150]}")

    # Look for JavaScript that might load data dynamically
    scripts = soup.find_all("script")
    print(f"\n  Scripts found: {len(scripts)}")

    for script in scripts:
        script_text = script.string or ""
        if "list" in script_text.lower() or "chart" in script_text.lower():
            print(f"    Found script with 'list' or 'chart' keyword")
            break

if __name__ == "__main__":
    try:
        fetch_list_page()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
