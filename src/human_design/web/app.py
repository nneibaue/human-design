"""
FastAPI web application for Human Design people browser.

Provides a DataTables-based UI for viewing and filtering people
from 64keys.com with custom tagging support.

64keys Chart URL Patterns (discovered 2026-01-30):
- Individual: /chart?id={id}
- Transit: /transit?id1={id}
- Interaction (2 people): /interaction?id1={id1}&id2={id2}
- Penta (3-5 people): /penta?id0={id}&id1={id}&id2={id}&id3={id}&id4={id}&s0=a&s1=a&s2=a&s3=a&s4=a
- Family Penta: /familypenta?id0={id}&id1={id}&id2={id}&id3={id}&id4={id}&s0=a&s1=a&s2=a&s3=a&s4=a
- Multi-chart (2-16): /multi_chart?id[0]={id}&id[1]={id}&...
- O16 (1-100): /o16?ids={id},{id},{id}
"""

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import boto3
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from ..api import GateAPI
from ..models.people import GroupStore, PeopleResponse, Person, RelationshipStore, TagStore


# Global state
_api: GateAPI | None = None
_tag_store: TagStore | None = None
_relationship_store: RelationshipStore | None = None
_group_store: GroupStore | None = None
_people_cache: dict[str, list[Person]] = {}
_tags_file: Path = Path("data/tags.json")
_relationships_file: Path = Path("data/relationships.json")
_groups_file: Path = Path("data/groups.json")

# S3 client (lazy initialization)
_s3_client = None


def _get_s3_client():
    """Get or create S3 client"""
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3")
    return _s3_client


def _get_data_bucket() -> str:
    """Get S3 data bucket name from env or fallback to local"""
    return os.environ.get("DATA_BUCKET", "")


def _load_json_from_s3_or_local(key: str, default: dict[str, Any]) -> dict[str, Any]:
    """Load JSON from S3 if DATA_BUCKET is set, otherwise use local file"""
    bucket = _get_data_bucket()

    # Use S3 if in AWS environment
    if bucket:
        try:
            s3 = _get_s3_client()
            response = s3.get_object(Bucket=bucket, Key=key)
            return json.loads(response["Body"].read())
        except s3.exceptions.NoSuchKey:
            # File doesn't exist yet, return default
            return default
        except Exception as e:
            print(f"Warning: Failed to load {key} from S3: {e}")
            return default

    # Fallback to local file (development)
    local_path = Path(f"data/{key}")
    if local_path.exists():
        with open(local_path) as f:
            return json.load(f)
    return default


def _save_json_to_s3_or_local(key: str, data: dict[str, Any]) -> None:
    """Save JSON to S3 if DATA_BUCKET is set, otherwise save locally"""
    bucket = _get_data_bucket()

    # Use S3 if in AWS environment
    if bucket:
        try:
            s3 = _get_s3_client()
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(data, indent=2),
                ContentType="application/json"
            )
        except Exception as e:
            print(f"Error: Failed to save {key} to S3: {e}")
            raise
    else:
        # Fallback to local file (development)
        local_path = Path(f"data/{key}")
        local_path.parent.mkdir(exist_ok=True)
        with open(local_path, "w") as f:
            json.dump(data, f, indent=2)


def get_api() -> GateAPI:
    """Get the authenticated 64keys API client."""
    global _api
    if _api is None:
        _api = GateAPI()
        _api.authenticate()
    return _api


def get_tag_store() -> TagStore:
    """Get the tag store, loading from S3 or disk if needed."""
    global _tag_store
    if _tag_store is None:
        data = _load_json_from_s3_or_local("tags.json", {"person_tags": {}})
        _tag_store = TagStore.model_validate(data)
    return _tag_store


def save_tag_store() -> None:
    """Save the tag store to S3 or disk."""
    store = get_tag_store()
    _save_json_to_s3_or_local("tags.json", store.model_dump())


def get_relationship_store() -> RelationshipStore:
    """Get the relationship store, loading from S3 or disk if needed."""
    global _relationship_store
    if _relationship_store is None:
        data = _load_json_from_s3_or_local("relationships.json", {"relationships": []})
        _relationship_store = RelationshipStore.model_validate(data)
    return _relationship_store


def save_relationship_store() -> None:
    """Save the relationship store to S3 or disk."""
    store = get_relationship_store()
    _save_json_to_s3_or_local("relationships.json", store.model_dump())


def get_group_store() -> GroupStore:
    """Get the group store, loading from S3 or disk if needed."""
    global _group_store
    if _group_store is None:
        data = _load_json_from_s3_or_local("groups.json", {"groups": []})
        _group_store = GroupStore.model_validate(data)
    return _group_store


def save_group_store() -> None:
    """Save the group store to S3 or disk."""
    store = get_group_store()
    _save_json_to_s3_or_local("groups.json", store.model_dump())


# 64keys group definitions - filter is the 'a' param value for filtered queries
GROUPS = {
    "allmine": {"t": "allmine", "filter": "", "label": "ALL", "color": "warning"},
    "family": {"t": "relation", "filter": "relfamilyclose", "label": "Family", "color": "primary"},
    "relatives": {
        "t": "relation",
        "filter": "relfamilywide",
        "label": "Relatives",
        "color": "primary",
    },
    "close_friends": {
        "t": "relation",
        "filter": "relfriend",
        "label": "Close Friends",
        "color": "primary",
    },
    "friends": {"t": "relation", "filter": "relbuddy", "label": "Friends", "color": "primary"},
    "business_partners": {
        "t": "relation",
        "filter": "relbusinesspartner",
        "label": "Business Partners",
        "color": "info",
    },
    "business_clients": {
        "t": "relation",
        "filter": "relcustomerbusiness",
        "label": "Business Clients",
        "color": "info",
    },
    "business_network": {
        "t": "relation",
        "filter": "relbusinessnetwork",
        "label": "Business Network",
        "color": "info",
    },
    "employees": {"t": "relation", "filter": "relemployee", "label": "Employees", "color": "info"},
    "third_persons": {
        "t": "relation",
        "filter": "relthird",
        "label": "Third Persons",
        "color": "secondary",
    },
    "candidates": {
        "t": "relation",
        "filter": "relcandidate",
        "label": "Candidates",
        "color": "secondary",
    },
    "private_clients": {
        "t": "relation",
        "filter": "relcustomerprivate",
        "label": "Private Clients",
        "color": "secondary",
    },
    "vips": {"t": "relation", "filter": "relvip", "label": "VIPs", "color": "warning"},
    "events": {"t": "event", "filter": "", "label": "Events", "color": "secondary"},
}


def fetch_people_from_64keys(group_key: str) -> list[Person]:
    """Fetch people from 64keys API for a specific group.

    64keys uses session-based filtering. You MUST visit /list_prepare first
    to set the session filter state, then call /list_api with a=list.
    """
    if group_key not in GROUPS:
        raise ValueError(f"Unknown group: {group_key}")

    group = GROUPS[group_key]
    api = get_api()

    # Step 1: Set the session filter by visiting list_prepare
    # This is REQUIRED - 64keys uses session-based filtering
    prepare_params = {
        "t": group["t"],
        "a": group["filter"],
    }
    api.session.get("https://www.64keys.com/list_prepare", params=prepare_params)

    # Step 2: Now call list_api - it will use the session filter
    # The 'a' param should always be 'list' - filtering is done via session
    params: dict[str, str] = {
        "a": "list",
        "t": group["t"],
        "_search": "false",
        "rows": "1000",
        "page": "1",
        "sidx": "lastname",
        "sord": "asc",
    }

    response = api.session.get("https://www.64keys.com/list_api", params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"64keys API error: {response.status_code}")

    # Handle empty or invalid responses
    if not response.text or response.text.strip() == "":
        return []

    try:
        data = response.json()
    except Exception:
        # If JSON parsing fails, return empty list
        return []

    rows = data.get("rows", [])

    people = []
    for row in rows:
        cell = row.get("cell", [])
        if cell:
            person = Person.from_cell(cell, groups=[group_key])
            people.append(person)

    return people


def fetch_all_people() -> list[Person]:
    """Fetch all people and track their group memberships."""
    global _people_cache

    # Use cached data if available
    if "all" in _people_cache:
        return _people_cache["all"]

    # Fetch from allmine to get everyone
    api = get_api()

    # Step 1: Set the session filter by visiting list_prepare
    # This is REQUIRED - 64keys uses session-based filtering
    api.session.get("https://www.64keys.com/list_prepare", params={"t": "allmine", "a": ""})

    # Step 2: Now call list_api - it will use the session filter
    params = {
        "a": "list",
        "t": "allmine",
        "_search": "false",
        "rows": "1000",
        "page": "1",
        "sidx": "lastname",
        "sord": "asc",
    }

    response = api.session.get("https://www.64keys.com/list_api", params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"64keys API error: {response.status_code}")

    data = response.json()
    rows = data.get("rows", [])

    # Build people list
    people_by_id: dict[int, Person] = {}
    for row in rows:
        cell = row.get("cell", [])
        if cell:
            person = Person.from_cell(cell, groups=["allmine"])
            people_by_id[person.id] = person

    # Apply custom tags
    tag_store = get_tag_store()
    for person in people_by_id.values():
        person.custom_tags = tag_store.get_tags(person.id)

    people = list(people_by_id.values())
    _people_cache["all"] = people

    return people


def clear_cache() -> None:
    """Clear the people cache."""
    global _people_cache
    _people_cache = {}


def _get_webapp_password() -> str:
    """Get webapp password from AWS Secrets Manager or environment variable."""
    secret_name = os.environ.get("WEBAPP_PASSWORD_SECRET")
    if secret_name:
        try:
            sm = boto3.client("secretsmanager")
            response = sm.get_secret_value(SecretId=secret_name)
            secret = json.loads(response["SecretString"])
            return secret.get("password", "")
        except Exception:
            pass
    # Fallback to environment variable
    return os.environ.get("WEBAPP_PASSWORD", "")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan handler."""
    # Startup: ensure data directory exists
    _tags_file.parent.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown: save tags
    if _tag_store is not None:
        save_tag_store()


# Create FastAPI app
app = FastAPI(
    title="Human Design People Browser",
    description="Browse and filter people from 64keys.com",
    version="0.1.0",
    lifespan=lifespan,
)

# Add session middleware for authentication
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY", "dev-secret-key-change-in-production"),
)

# Templates
templates_dir = Path(__file__).parent / "templates"
# Only create templates directory if it doesn't exist (for local dev)
# In Lambda, the directory is read-only and already exists from the package
if not templates_dir.exists():
    templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


# ============================================================================
# Authentication
# ============================================================================


@app.post("/login")
async def login(request: Request) -> RedirectResponse:
    """Login endpoint that verifies password and sets session."""
    try:
        form_data = await request.form()
        pwd = form_data.get("password", "")
    except Exception:
        pwd = ""

    if pwd == _get_webapp_password():
        request.session["authenticated"] = True
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url="/login?error=Invalid+password", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = "") -> HTMLResponse:
    """Login page."""
    # Check if already authenticated
    if request.session.get("authenticated"):
        return RedirectResponse(url="/", status_code=303)

    error_msg = error if error else ""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Human Design</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #4a2c6a 0%, #6b4190 100%); margin: 0; }}
            .login-box {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); width: 300px; }}
            h1 {{ text-align: center; color: #4a2c6a; margin-top: 0; }}
            input {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
            button {{ width: 100%; padding: 10px; background: #6b4190; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
            button:hover {{ background: #4a2c6a; }}
            .error {{ color: red; margin: 10px 0; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>Human Design</h1>
            {f'<div class="error">⚠️ {error_msg}</div>' if error_msg else ''}
            <form method="post">
                <input type="password" name="password" placeholder="Password" required autofocus>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """


def require_auth(func):  # type: ignore
    """Decorator to require authentication for a route."""
    async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:  # type: ignore
        if not request.session.get("authenticated"):
            return RedirectResponse(url="/login", status_code=303)
        return await func(request, *args, **kwargs)
    return wrapper


# Routes


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Landing page with DataTables."""
    # Check authentication
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "groups": GROUPS,
        },
    )


@app.get("/api/people", response_model=PeopleResponse)
async def get_people(
    group: str = Query(default="allmine", description="Group to filter by"),
    refresh: bool = Query(default=False, description="Force refresh from 64keys"),
) -> PeopleResponse:
    """Get people from 64keys, optionally filtered by group."""
    if refresh:
        clear_cache()

    if group == "allmine" or group == "all":
        people = fetch_all_people()
    else:
        people = fetch_people_from_64keys(group)

    return PeopleResponse(total=len(people), people=people)


@app.get("/api/people/{person_id}")
async def get_person(person_id: int) -> Person:
    """Get a single person by ID."""
    people = fetch_all_people()
    for person in people:
        if person.id == person_id:
            return person
    raise HTTPException(status_code=404, detail=f"Person {person_id} not found")


@app.post("/api/people/{person_id}/tags/{tag}")
async def add_tag(person_id: int, tag: str) -> dict[str, Any]:
    """Add a custom tag to a person."""
    store = get_tag_store()
    store.add_tag(person_id, tag)
    save_tag_store()

    # Update cache
    if "all" in _people_cache:
        for person in _people_cache["all"]:
            if person.id == person_id:
                person.custom_tags = store.get_tags(person_id)
                break

    return {"status": "ok", "tags": store.get_tags(person_id)}


@app.delete("/api/people/{person_id}/tags/{tag}")
async def remove_tag(person_id: int, tag: str) -> dict[str, Any]:
    """Remove a custom tag from a person."""
    store = get_tag_store()
    store.remove_tag(person_id, tag)
    save_tag_store()

    # Update cache
    if "all" in _people_cache:
        for person in _people_cache["all"]:
            if person.id == person_id:
                person.custom_tags = store.get_tags(person_id)
                break

    return {"status": "ok", "tags": store.get_tags(person_id)}


@app.get("/api/tags")
async def get_all_tags() -> dict[str, Any]:
    """Get all unique custom tags."""
    store = get_tag_store()
    return {"tags": store.all_tags()}


@app.post("/api/refresh")
async def refresh_data() -> dict[str, Any]:
    """Force refresh data from 64keys."""
    clear_cache()
    people = fetch_all_people()
    return {"status": "ok", "count": len(people)}


@app.get("/api/groups")
async def get_groups() -> dict[str, Any]:
    """Get available groups."""
    return {"groups": GROUPS}


# ============================================================================
# Chart URL Generation Endpoints
# ============================================================================


@app.get("/api/chart-urls")
async def get_chart_urls(
    ids: str = Query(..., description="Comma-separated person IDs"),
) -> dict[str, Any]:
    """Generate 64keys chart URLs for a selection of people.

    Returns URLs for:
    - Individual charts (all selected)
    - Interaction (if exactly 2 selected)
    - Penta/Family Penta (if 3-5 selected)
    - Multi-chart (if 2-16 selected)
    - O16 (if 1-100 selected)
    - Transit (for first person)
    """
    id_list = [int(id.strip()) for id in ids.split(",") if id.strip()]
    count = len(id_list)

    base_url = "https://www.64keys.com"
    urls: dict[str, Any] = {}

    # Individual charts for all
    urls["individual"] = [f"{base_url}/chart?id={id}" for id in id_list]

    # Transit for first person
    if count >= 1:
        urls["transit"] = f"{base_url}/transit?id1={id_list[0]}"

    # Interaction - exactly 2 people
    if count == 2:
        urls["interaction"] = f"{base_url}/interaction?id1={id_list[0]}&id2={id_list[1]}"
    else:
        urls["interaction"] = None

    # Family Penta - 3 to 5 people
    # 64keys JS uses 'undefined' for empty slots
    if 3 <= count <= 5:
        padded = id_list + [None] * (5 - count)
        penta_params = "&".join(
            [f"id{i}={padded[i] if padded[i] else 'undefined'}" for i in range(5)]
            + [f"s{i}=a" for i in range(5)]
        )
        urls["family_penta"] = f"{base_url}/familypenta?{penta_params}"
    else:
        urls["family_penta"] = None

    # Multi-chart - 2 to 16 people
    if 2 <= count <= 16:
        multi_params = "&".join([f"id[{i}]={id_list[i]}" for i in range(count)])
        urls["multi_chart"] = f"{base_url}/multi_chart?{multi_params}"
    else:
        urls["multi_chart"] = None

    # O16 - 1 to 100 people
    if 1 <= count <= 100:
        urls["o16"] = f"{base_url}/o16?ids={','.join(map(str, id_list))}"
    else:
        urls["o16"] = None

    return {"count": count, "ids": id_list, "urls": urls}


# ============================================================================
# Relationship Endpoints
# ============================================================================


@app.get("/api/relationships")
async def get_all_relationships() -> dict[str, Any]:
    """Get all stored relationships."""
    store = get_relationship_store()
    return {"relationships": [r.model_dump() for r in store.relationships]}


@app.get("/api/relationships/{person_id}")
async def get_person_relationships(person_id: int) -> dict[str, Any]:
    """Get relationships for a specific person."""
    store = get_relationship_store()
    outgoing = store.get_relationships_for(person_id)
    incoming = store.get_relationships_to(person_id)
    return {
        "person_id": person_id,
        "outgoing": [r.model_dump() for r in outgoing],
        "incoming": [r.model_dump() for r in incoming],
        "all_related_ids": store.get_all_related(person_id),
    }


@app.post("/api/relationships")
async def add_relationship(
    from_id: int = Query(...),
    to_id: int = Query(...),
    relationship: str = Query(...),
    notes: str = Query(default=""),
) -> dict[str, Any]:
    """Add or update a relationship between two people."""
    store = get_relationship_store()
    store.add_relationship(from_id, to_id, relationship, notes)
    save_relationship_store()
    return {
        "status": "ok",
        "relationship": {
            "from_id": from_id,
            "to_id": to_id,
            "relationship": relationship,
        },
    }


@app.delete("/api/relationships")
async def delete_relationship(from_id: int = Query(...), to_id: int = Query(...)) -> dict[str, Any]:
    """Remove a relationship between two people."""
    store = get_relationship_store()
    store.remove_relationship(from_id, to_id)
    save_relationship_store()
    return {"status": "ok"}


# ============================================================================
# Humun Group Endpoints (custom groups, not 64keys categories)
# ============================================================================


@app.get("/api/humun-groups")
async def get_all_humun_groups() -> dict[str, Any]:
    """Get all custom humun groups."""
    store = get_group_store()
    return {"groups": [g.model_dump() for g in store.groups]}


@app.post("/api/humun-groups")
async def create_humun_group(
    name: str = Query(...),
    owner_id: int | None = Query(default=None),
    description: str = Query(default=""),
) -> dict[str, Any]:
    """Create a new custom humun group."""
    store = get_group_store()
    group = store.add_group(name, owner_id, description)
    save_group_store()
    return {"status": "ok", "group": group.model_dump()}


@app.post("/api/humun-groups/{group_name}/members/{person_id}")
async def add_group_member(group_name: str, person_id: int) -> dict[str, Any]:
    """Add a person to a humun group."""
    store = get_group_store()
    store.add_member(group_name, person_id)
    save_group_store()
    group = store.get_group(group_name)
    return {"status": "ok", "group": group.model_dump() if group else None}


@app.delete("/api/humun-groups/{group_name}/members/{person_id}")
async def remove_group_member(group_name: str, person_id: int) -> dict[str, Any]:
    """Remove a person from a humun group."""
    store = get_group_store()
    store.remove_member(group_name, person_id)
    save_group_store()
    group = store.get_group(group_name)
    return {"status": "ok", "group": group.model_dump() if group else None}


@app.delete("/api/humun-groups/{group_name}")
async def delete_humun_group(group_name: str) -> dict[str, Any]:
    """Delete a humun group."""
    store = get_group_store()
    store.delete_group(group_name)
    save_group_store()
    return {"status": "ok"}
