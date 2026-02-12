"""
Web browsing tools for the 64keys MCP server.
"""

from typing import Annotated
from urllib.parse import urljoin, urlparse

import markdownify
from bs4 import BeautifulSoup
from mcp.server.fastmcp import Context
from pydantic import Field

from ..session import SessionManager


async def fetch_page(
    url: Annotated[str, Field(description="URL to fetch (absolute or relative to 64keys.com)")],
    max_length: Annotated[int, Field(description="Max characters to return")] = 8000,
    start_index: Annotated[int, Field(description="Start index for pagination")] = 0,
    ctx: Context | None = None,
) -> str:
    """
    Fetch a page from 64keys.com and convert to markdown.

    Returns the page content as markdown text, truncated if needed.
    Use start_index for pagination through long pages.
    """
    session: SessionManager = ctx.request_context.lifespan_context  # type: ignore

    # Normalize URL
    if not url.startswith("http"):
        url = urljoin(session.BASE_URL, url)

    # Validate it's a 64keys URL
    parsed = urlparse(url)
    if "64keys.com" not in parsed.netloc:
        return f"Error: URL must be on 64keys.com domain, got {parsed.netloc}"

    try:
        response = await session.get(url)
        response.raise_for_status()
    except Exception as e:
        return f"Error fetching URL: {e}"

    # Convert HTML to markdown
    content = markdownify.markdownify(
        response.text,
        heading_style="ATX",
        strip=["script", "style", "nav"],
    )

    # Clean up excessive whitespace
    lines = [line.strip() for line in content.split("\n")]
    content = "\n".join(line for line in lines if line)

    # Handle pagination
    original_length = len(content)
    truncated = content[start_index : start_index + max_length]

    if len(truncated) == max_length and start_index + max_length < original_length:
        remaining = original_length - (start_index + max_length)
        truncated += f"\n\n[Truncated. {remaining} chars remaining. "
        truncated += f"Call with start_index={start_index + max_length} for more]"

    return truncated


async def extract_links(
    url: Annotated[str, Field(description="URL to extract links from")],
    filter_text: Annotated[
        str | None, Field(description="Optional text to filter links by")
    ] = None,
    ctx: Context | None = None,
) -> list[dict[str, str]]:
    """
    Extract all links from a 64keys page.

    Returns a list of {text, href, full_url} for each link found.
    Use filter_text to find specific links.
    """
    session: SessionManager = ctx.request_context.lifespan_context  # type: ignore

    # Normalize URL
    if not url.startswith("http"):
        url = urljoin(session.BASE_URL, url)

    try:
        response = await session.get(url)
        response.raise_for_status()
    except Exception as e:
        return [{"error": str(e)}]

    soup = BeautifulSoup(response.text, "html.parser")
    links: list[dict[str, str]] = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True) or "[no text]"

        # Skip empty or javascript links
        if not href or href.startswith("javascript:") or href == "#":
            continue

        # Build full URL
        full_url = urljoin(url, href)

        # Apply filter if provided
        if filter_text:
            if filter_text.lower() not in text.lower() and filter_text.lower() not in href.lower():
                continue

        links.append({"text": text, "href": href, "full_url": full_url})

    # Deduplicate by full_url
    seen: set[str] = set()
    unique_links: list[dict[str, str]] = []
    for link in links:
        if link["full_url"] not in seen:
            seen.add(link["full_url"])
            unique_links.append(link)

    return unique_links


async def click_link(
    url: Annotated[str, Field(description="Current page URL")],
    link_text: Annotated[str, Field(description="Text of the link to click")],
    max_length: Annotated[int, Field(description="Max characters to return")] = 8000,
    ctx: Context | None = None,
) -> str:
    """
    Find a link by its text on a page and fetch the target page.

    Simulates clicking a link by finding it on the page and fetching its target.
    """
    # First extract links from the page
    links = await extract_links(url, filter_text=link_text, ctx=ctx)

    if not links:
        return f"No link found matching '{link_text}'"

    if "error" in links[0]:
        return f"Error: {links[0]['error']}"

    # Use the first matching link
    target_url = links[0]["full_url"]
    matched_text = links[0]["text"]

    # Fetch the target page
    content = await fetch_page(target_url, max_length=max_length, ctx=ctx)

    return f"Clicked: '{matched_text}' → {target_url}\n\n{content}"


async def search_page(
    url: Annotated[str, Field(description="URL to search")],
    query: Annotated[str, Field(description="Text to search for (case-insensitive)")],
    context_chars: Annotated[int, Field(description="Characters of context around matches")] = 200,
    ctx: Context | None = None,
) -> list[dict[str, str | int]]:
    """
    Search for text on a 64keys page.

    Returns matches with surrounding context.
    """
    session: SessionManager = ctx.request_context.lifespan_context  # type: ignore

    # Normalize URL
    if not url.startswith("http"):
        url = urljoin(session.BASE_URL, url)

    try:
        response = await session.get(url)
        response.raise_for_status()
    except Exception as e:
        return [{"error": str(e)}]

    # Get text content
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "nav"]):
        element.decompose()

    text = soup.get_text(separator=" ", strip=True)

    # Find all matches
    matches: list[dict[str, str | int]] = []
    query_lower = query.lower()
    text_lower = text.lower()

    pos = 0
    while True:
        idx = text_lower.find(query_lower, pos)
        if idx == -1:
            break

        # Extract context
        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(query) + context_chars)
        context = text[start:end]

        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        matches.append({"position": idx, "context": context})

        pos = idx + 1
        if len(matches) >= 20:  # Limit matches
            break

    return matches


async def get_page_structure(
    url: Annotated[str, Field(description="URL to analyze")],
    ctx: Context | None = None,
) -> dict[str, list[str] | int]:
    """
    Get the structure of a 64keys page.

    Returns headings, forms, buttons, and other structural elements.
    """
    session: SessionManager = ctx.request_context.lifespan_context  # type: ignore

    # Normalize URL
    if not url.startswith("http"):
        url = urljoin(session.BASE_URL, url)

    try:
        response = await session.get(url)
        response.raise_for_status()
    except Exception as e:
        return {"error": [str(e)]}

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract structure
    structure: dict[str, list[str] | int] = {
        "title": [],
        "headings": [],
        "forms": [],
        "buttons": [],
        "inputs": [],
        "link_count": 0,
    }

    # Title
    title = soup.find("title")
    if title:
        structure["title"] = [title.get_text(strip=True)]

    # Headings
    for tag in ["h1", "h2", "h3", "h4"]:
        for h in soup.find_all(tag):
            text = h.get_text(strip=True)
            if text:
                structure["headings"].append(f"{tag}: {text}")  # type: ignore

    # Forms
    for form in soup.find_all("form"):
        action = form.get("action", "[no action]")
        method = form.get("method", "get").upper()
        structure["forms"].append(f"{method} {action}")  # type: ignore

    # Buttons
    for btn in soup.find_all(["button", "input"]):
        if btn.name == "button" or btn.get("type") in ["submit", "button"]:
            text = btn.get_text(strip=True) or btn.get("value", "[no text]")
            structure["buttons"].append(text)  # type: ignore

    # Input fields
    for inp in soup.find_all("input"):
        input_type = inp.get("type", "text")
        name = inp.get("name", "[unnamed]")
        if input_type not in ["hidden", "submit", "button"]:
            structure["inputs"].append(f"{name} ({input_type})")  # type: ignore

    # Link count
    structure["link_count"] = len(soup.find_all("a", href=True))

    return structure
