"""
64keys domain-specific tools for the MCP server.
"""

from typing import Annotated
from urllib.parse import urljoin

import markdownify
from bs4 import BeautifulSoup
from mcp.server.fastmcp import Context
from pydantic import Field

from ..session import SessionManager

# Group definitions for list_api
GROUPS = {
    "allmine": {"t": "allmine", "filter": "", "label": "All My People"},
    "family": {"t": "relation", "filter": "relfamilyclose", "label": "Family"},
    "relatives": {"t": "relation", "filter": "relfamilywide", "label": "Relatives"},
    "close_friends": {"t": "relation", "filter": "relfriend", "label": "Close Friends"},
    "friends": {"t": "relation", "filter": "relbuddy", "label": "Friends"},
    "business_partners": {"t": "relation", "filter": "relbusinesspartner", "label": "Partners"},
    "business_clients": {"t": "relation", "filter": "relcustomerbusiness", "label": "Clients"},
    "business_network": {"t": "relation", "filter": "relbusinessnetwork", "label": "Network"},
    "employees": {"t": "relation", "filter": "relemployee", "label": "Employees"},
    "vips": {"t": "relation", "filter": "relvip", "label": "VIPs"},
}


async def list_people(
    group: Annotated[
        str,
        Field(
            description="Group to list: allmine, family, relatives, close_friends, friends, "
            "business_partners, business_clients, business_network, employees, vips"
        ),
    ] = "allmine",
    limit: Annotated[int, Field(description="Max number of people to return")] = 50,
    ctx: Context | None = None,
) -> list[dict]:
    """
    List people from your 64keys account.

    Returns basic info for each person including id, name, type, profile.

    NOTE: 64keys uses session-based filtering. For filtered groups,
    we first visit /list_prepare to set the session filter, then call the API.
    """
    session: SessionManager = ctx.request_context.lifespan_context  # type: ignore

    if group not in GROUPS:
        return [{"error": f"Unknown group. Valid: {list(GROUPS.keys())}"}]

    group_def = GROUPS[group]

    # Step 1: Set the session filter by visiting list_prepare
    # This is how 64keys handles filtering - session-based state
    prepare_url = f"{session.BASE_URL}/list_prepare"
    prepare_params = {
        "t": group_def["t"],
        "a": group_def["filter"],
    }
    try:
        await session.get(prepare_url, params=prepare_params)
    except Exception:
        pass  # Continue even if this fails

    # Step 2: Now call list_api - it will use the session filter
    # The 'a' param should always be 'list' - filtering is done via session
    params = {
        "a": "list",
        "t": group_def["t"],
        "_search": "false",
        "rows": str(min(limit, 1000)),
        "page": "1",
        "sidx": "lastname",
        "sord": "asc",
    }

    url = f"{session.BASE_URL}/list_api"

    try:
        response = await session.get(url, params=params)
        response.raise_for_status()
    except Exception as e:
        return [{"error": str(e)}]

    # Handle empty responses
    if not response.text.strip():
        return []

    try:
        data = response.json()
    except Exception:
        return []

    rows = data.get("rows", [])
    people = []

    for row in rows[:limit]:
        cell = row.get("cell", [])
        if not cell or len(cell) < 30:
            continue

        # Extract key fields from cell array
        # Based on jqGrid colModel from 64keys:
        # 0=nr, 1=lastname, 2=firstname, 3=gender, 4=customAge, 5=maintype
        # 6=xingnameshort (cross), 7=modus (profile), 8=crossgates, 9=definitions
        # 10=channelstext, 11=zodiac, 12=customDate, 13=customTime, 14=birthdatevariance
        # 15=birthcountryshort, 16=birthcity
        # ...
        # 86=relatedby, 87=families, 88=tagsastext
        people.append(
            {
                "id": row.get("id", cell[0] if cell else None),
                "lastname": cell[1] if len(cell) > 1 else "",
                "firstname": cell[2] if len(cell) > 2 else "",
                "gender": cell[3] if len(cell) > 3 else "",
                "age": cell[4] if len(cell) > 4 else "",
                "maintype": cell[5] if len(cell) > 5 else "",
                "cross_name": cell[6] if len(cell) > 6 else "",
                "profile": cell[7] if len(cell) > 7 else "",
                "cross_gates": cell[8] if len(cell) > 8 else "",
                "definitions": cell[9] if len(cell) > 9 else "",
                "channels": cell[10] if len(cell) > 10 else "",
                "zodiac": cell[11] if len(cell) > 11 else "",
                "birth_date": cell[12] if len(cell) > 12 else "",
                "birth_time": cell[13] if len(cell) > 13 else "",
                "birth_variance": cell[14] if len(cell) > 14 else "",
                "birth_country": cell[15] if len(cell) > 15 else "",
                "birth_city": cell[16] if len(cell) > 16 else "",
                "related_by": cell[86] if len(cell) > 86 else "",
                "families": cell[87] if len(cell) > 87 else "",
                "tags": cell[88] if len(cell) > 88 else "",
                "chart_url": f"https://www.64keys.com/chart?id={row.get('id', cell[0] if cell else '')}",
            }
        )

    return people


async def get_person_chart(
    person_id: Annotated[int, Field(description="64keys person/design ID")],
    ctx: Context | None = None,
) -> str:
    """
    Get the Human Design chart page for a specific person.

    Returns the chart content as markdown.
    """
    session: SessionManager = ctx.request_context.lifespan_context  # type: ignore

    url = f"{session.BASE_URL}/chart?id={person_id}"

    try:
        response = await session.get(url)
        response.raise_for_status()
    except Exception as e:
        return f"Error fetching chart: {e}"

    # Convert to markdown
    content = markdownify.markdownify(
        response.text,
        heading_style="ATX",
        strip=["script", "style", "nav"],
    )

    # Clean up
    lines = [line.strip() for line in content.split("\n")]
    content = "\n".join(line for line in lines if line)

    # Truncate if too long
    if len(content) > 10000:
        content = content[:10000] + "\n\n[Truncated]"

    return content


async def get_gate(
    gate_number: Annotated[int, Field(description="Gate number (1-64)")],
    ctx: Context | None = None,
) -> dict:
    """
    Get detailed information about a Human Design gate from 64keys.

    Returns gate name, summary, description, and line information.
    """
    session: SessionManager = ctx.request_context.lifespan_context  # type: ignore

    if not 1 <= gate_number <= 64:
        return {"error": "Gate number must be between 1 and 64"}

    url = f"{session.BASE_URL}/library_api"
    params = {"type": "gate", "param1": str(gate_number)}

    try:
        response = await session.get(url, params=params)
        response.raise_for_status()
    except Exception as e:
        return {"error": str(e)}

    soup = BeautifulSoup(response.text, "html.parser")
    container = soup.find("div", {"id": "aspectscontainer"})

    if not container:
        return {"error": "Could not find gate container in response"}

    result: dict = {"gate_number": gate_number}

    # Extract basic info
    gate_num_elem = container.find("div", {"class": "gatenumber"})  # type: ignore
    name_elem = container.find("div", {"class": "gatesubline"})  # type: ignore
    quarter_elem = container.find("div", {"class": "qinfo"})  # type: ignore
    summary_elem = container.find("div", {"class": "gatetext"})  # type: ignore

    if gate_num_elem:
        result["gate_label"] = gate_num_elem.text.strip()
    if name_elem:
        result["name"] = name_elem.text.strip()
    if quarter_elem:
        result["quarter"] = quarter_elem.text.strip().replace("Quarter: ", "")
    if summary_elem:
        result["summary"] = summary_elem.text.strip()

    # Extract description
    description_elems = container.find_all("div", {"class": "potentialgatetext"})  # type: ignore
    if description_elems:
        result["description"] = description_elems[0].text.strip()

    # Extract lines
    lines = []
    line_headlines = container.find_all("div", {"class": "potentialgateheadline"})  # type: ignore

    for headline in line_headlines:
        line_text = headline.text.strip()
        if "." in line_text and line_text[0].isdigit():
            try:
                line_number = int(line_text.split(".")[1])
                if 1 <= line_number <= 6:
                    title_elem = headline.find_next("div", {"class": "gatesubline"})
                    text_elem = (
                        title_elem.find_next("div", {"class": "gatetext"}) if title_elem else None
                    )

                    lines.append(
                        {
                            "line": line_number,
                            "title": title_elem.text.strip() if title_elem else "",
                            "text": text_elem.text.strip() if text_elem else "",
                        }
                    )
            except (ValueError, AttributeError):
                continue

    result["lines"] = lines

    return result


async def search_library(
    query: Annotated[str, Field(description="Search term for the 64keys library")],
    search_type: Annotated[
        str, Field(description="Type to search: gate, channel, center, or all")
    ] = "all",
    ctx: Context | None = None,
) -> list[dict]:
    """
    Search the 64keys library for gates, channels, or centers.

    Returns matching items with basic info.
    """
    session: SessionManager = ctx.request_context.lifespan_context  # type: ignore

    # For now, search gates by fetching the library page
    url = f"{session.BASE_URL}/library"

    try:
        response = await session.get(url)
        response.raise_for_status()
    except Exception as e:
        return [{"error": str(e)}]

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[dict] = []
    query_lower = query.lower()

    # Search through the page content
    for element in soup.find_all(["a", "div", "span"]):
        text = element.get_text(strip=True).lower()
        if query_lower in text:
            href = element.get("href", "") if element.name == "a" else ""
            results.append(
                {
                    "text": element.get_text(strip=True)[:200],
                    "element": element.name,
                    "href": href,
                    "full_url": urljoin(session.BASE_URL, href) if href else "",
                }
            )

    # Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for r in results:
        key = r["text"][:50]
        if key not in seen:
            seen.add(key)
            unique.append(r)
        if len(unique) >= 20:
            break

    return unique


async def get_transit(
    ctx: Context | None = None,
) -> str:
    """
    Get the current transit (planetary positions) from 64keys.

    Returns the transit chart information as markdown.
    """
    session: SessionManager = ctx.request_context.lifespan_context  # type: ignore

    url = f"{session.BASE_URL}/transit"

    try:
        response = await session.get(url)
        response.raise_for_status()
    except Exception as e:
        return f"Error fetching transit: {e}"

    content = markdownify.markdownify(
        response.text,
        heading_style="ATX",
        strip=["script", "style", "nav"],
    )

    # Clean up
    lines = [line.strip() for line in content.split("\n")]
    content = "\n".join(line for line in lines if line)

    if len(content) > 8000:
        content = content[:8000] + "\n\n[Truncated]"

    return content
