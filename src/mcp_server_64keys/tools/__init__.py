"""
Tools package for the 64keys MCP server.
"""

from .browsing import (
    click_link,
    extract_links,
    fetch_page,
    get_page_structure,
    search_page,
)
from .domain import (
    get_gate,
    get_person_chart,
    get_transit,
    list_people,
    search_library,
)

__all__ = [
    # Browsing tools
    "fetch_page",
    "extract_links",
    "click_link",
    "search_page",
    "get_page_structure",
    # Domain tools
    "list_people",
    "get_person_chart",
    "get_gate",
    "search_library",
    "get_transit",
]
