"""
64keys MCP Server

Provides tools for browsing, scraping, and interacting with 64keys.com
Human Design data through Claude and other MCP clients.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from .session import SessionManager
from .tools import (
    click_link,
    extract_links,
    fetch_page,
    get_gate,
    get_page_structure,
    get_person_chart,
    get_transit,
    list_people,
    search_library,
    search_page,
)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[SessionManager]:
    """
    Manage the authenticated session for all tool calls.

    Yields a SessionManager that handles auth and crawl delays.
    """
    async with SessionManager(crawl_delay=0.5) as session:
        yield session


# Create the MCP server
mcp = FastMCP(
    "64keys",
    instructions="""
    You are a 64keys.com assistant with full access to browse and interact with the website.

    Available capabilities:
    - Browse any page on 64keys.com and extract information
    - List and search people in the user's account
    - Get detailed gate, channel, and chart information
    - Follow links to explore the site

    For comprehensive browsing:
    1. Use fetch_page to get page content as markdown
    2. Use extract_links to find available navigation options
    3. Use click_link to follow links by their text
    4. Use get_page_structure to understand page layout

    For Human Design data:
    1. Use list_people to get people from the account
    2. Use get_person_chart to view someone's chart
    3. Use get_gate to get detailed gate information
    4. Use get_transit to see current planetary transits
    """,
    lifespan=lifespan,
)


# Register browsing tools
@mcp.tool()
async def browse_page(
    url: Annotated[str, Field(description="URL to fetch (absolute or relative to 64keys.com)")],
    max_length: Annotated[int, Field(description="Max characters to return")] = 8000,
    start_index: Annotated[int, Field(description="Start index for pagination")] = 0,
    ctx: Context = None,  # type: ignore
) -> str:
    """Fetch a page from 64keys.com and convert to readable markdown."""
    return await fetch_page(url, max_length, start_index, ctx)


@mcp.tool()
async def get_links(
    url: Annotated[str, Field(description="URL to extract links from")],
    filter_text: Annotated[str | None, Field(description="Optional text to filter links")] = None,
    ctx: Context = None,  # type: ignore
) -> list[dict[str, str]]:
    """Extract all clickable links from a 64keys page."""
    return await extract_links(url, filter_text, ctx)


@mcp.tool()
async def follow_link(
    url: Annotated[str, Field(description="Current page URL")],
    link_text: Annotated[str, Field(description="Text of the link to click")],
    max_length: Annotated[int, Field(description="Max characters to return")] = 8000,
    ctx: Context = None,  # type: ignore
) -> str:
    """Find a link by text and navigate to it, returning the target page."""
    return await click_link(url, link_text, max_length, ctx)


@mcp.tool()
async def find_text(
    url: Annotated[str, Field(description="URL to search")],
    query: Annotated[str, Field(description="Text to search for")],
    context_chars: Annotated[int, Field(description="Context chars around matches")] = 200,
    ctx: Context = None,  # type: ignore
) -> list[dict[str, str | int]]:
    """Search for text on a 64keys page and return matches with context."""
    return await search_page(url, query, context_chars, ctx)


@mcp.tool()
async def analyze_page(
    url: Annotated[str, Field(description="URL to analyze")],
    ctx: Context = None,  # type: ignore
) -> dict[str, list[str] | int]:
    """Get the structural elements of a page (headings, forms, buttons, etc.)."""
    return await get_page_structure(url, ctx)


# Register domain tools
@mcp.tool()
async def get_people(
    group: Annotated[
        str,
        Field(
            description="Group: allmine, family, relatives, close_friends, friends, "
            "business_partners, business_clients, business_network, employees, vips"
        ),
    ] = "allmine",
    limit: Annotated[int, Field(description="Max people to return")] = 50,
    ctx: Context = None,  # type: ignore
) -> list[dict]:
    """List people from your 64keys account."""
    return await list_people(group, limit, ctx)


@mcp.tool()
async def get_chart(
    person_id: Annotated[int, Field(description="64keys person/design ID")],
    ctx: Context = None,  # type: ignore
) -> str:
    """Get the Human Design chart for a specific person."""
    return await get_person_chart(person_id, ctx)


@mcp.tool()
async def get_gate_info(
    gate_number: Annotated[int, Field(description="Gate number (1-64)")],
    ctx: Context = None,  # type: ignore
) -> dict:
    """Get detailed information about a Human Design gate."""
    return await get_gate(gate_number, ctx)


@mcp.tool()
async def search_64keys(
    query: Annotated[str, Field(description="Search term")],
    search_type: Annotated[str, Field(description="Type: gate, channel, center, or all")] = "all",
    ctx: Context = None,  # type: ignore
) -> list[dict]:
    """Search the 64keys library for gates, channels, or centers."""
    return await search_library(query, search_type, ctx)


@mcp.tool()
async def get_current_transit(
    ctx: Context = None,  # type: ignore
) -> str:
    """Get the current transit (planetary positions) from 64keys."""
    return await get_transit(ctx)


# Resources
@mcp.resource("64keys://gate/{gate_number}")
async def gate_resource(gate_number: int) -> str:
    """Get gate information as a resource."""
    async with SessionManager() as session:
        # Create a minimal context
        from types import SimpleNamespace

        mock_ctx = SimpleNamespace()
        mock_ctx.request_context = SimpleNamespace()
        mock_ctx.request_context.lifespan_context = session

        result = await get_gate(gate_number, mock_ctx)  # type: ignore
        if "error" in result:
            return f"Error: {result['error']}"

        lines_text = ""
        for line in result.get("lines", []):
            lines_text += f"\n### Line {line['line']}: {line['title']}\n{line['text']}\n"

        return f"""# Gate {gate_number}: {result.get("name", "Unknown")}

**Quarter:** {result.get("quarter", "Unknown")}

## Summary
{result.get("summary", "")}

## Description
{result.get("description", "")}

## Lines
{lines_text}
"""


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
