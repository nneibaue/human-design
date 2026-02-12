"""
Async session manager for 64keys.com.

Handles authentication, CSRF tokens, and cookie management using httpx.
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from bs4 import BeautifulSoup


def _get_credentials() -> tuple[str, str]:
    """Get credentials from environment variables."""
    username = os.environ.get("HD_USERNAME")
    password = os.environ.get("HD_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Missing credentials. Set HD_USERNAME and HD_PASSWORD environment variables."
        )

    return username, password


def _get_session_cache_path() -> Path:
    """Get the path to the session cache file."""
    config_dir = Path.home() / ".config" / "human-design"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "session_async.json"


def _load_cached_cookies() -> dict[str, str] | None:
    """Load cached session cookies from disk."""
    cache_path = _get_session_cache_path()
    if cache_path.exists():
        try:
            with open(cache_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _save_cookies(cookies: httpx.Cookies) -> None:
    """Save session cookies to disk."""
    cache_path = _get_session_cache_path()
    try:
        cookie_dict = dict(cookies)
        with open(cache_path, "w") as f:
            json.dump(cookie_dict, f)
    except OSError:
        pass


@dataclass
class SessionManager:
    """
    Async session manager for 64keys.com with authentication.

    Usage:
        async with SessionManager() as session:
            response = await session.get("https://www.64keys.com/main")
    """

    BASE_URL: str = "https://www.64keys.com"
    LOGIN_URL: str = "https://www.64keys.com/login"
    HOME_URL: str = "https://www.64keys.com/main"

    client: httpx.AsyncClient = field(default=None, init=False)  # type: ignore
    is_authenticated: bool = field(default=False, init=False)
    crawl_delay: float = 0.5
    _last_request_time: float = field(default=0.0, init=False)

    async def __aenter__(self) -> "SessionManager":
        """Initialize the async client."""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "64KeysMCP/1.0 (Human Design Research)"},
        )

        # Try to load cached cookies
        cached_cookies = _load_cached_cookies()
        if cached_cookies:
            for name, value in cached_cookies.items():
                self.client.cookies.set(name, value)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Close the async client."""
        if self.client:
            await self.client.aclose()

    async def _apply_crawl_delay(self) -> None:
        """Apply crawl delay between requests."""
        if self.crawl_delay > 0 and self._last_request_time > 0:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self.crawl_delay:
                await asyncio.sleep(self.crawl_delay - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def authenticate(self) -> None:
        """Authenticate with 64keys.com."""
        username, password = _get_credentials()

        # Get login page to grab CSRF token
        await self._apply_crawl_delay()
        login_page = await self.client.get(self.LOGIN_URL)
        soup = BeautifulSoup(login_page.text, "html.parser")

        csrf_meta = soup.find("meta", {"name": "csrf-token"})
        if not csrf_meta:
            raise ValueError("Could not find CSRF token on login page")
        csrf_token = csrf_meta["content"]  # type: ignore

        # Login with CSRF token
        login_data = {"name": username, "password": password, "remember": "on"}
        await self._apply_crawl_delay()
        response = await self.client.post(
            self.LOGIN_URL,
            data=login_data,
            headers={"X-CSRF-TOKEN": str(csrf_token)},
        )

        if response.status_code != 200:
            raise httpx.HTTPStatusError(
                f"Authentication failed with status {response.status_code}",
                request=response.request,
                response=response,
            )

        # Save cookies for future use
        _save_cookies(self.client.cookies)
        self.is_authenticated = True

    async def _is_session_valid(self) -> bool:
        """Check if the cached session is still valid."""
        if not self.client.cookies:
            return False

        try:
            await self._apply_crawl_delay()
            response = await self.client.get(self.HOME_URL)
            # Check if we're redirected to login
            return response.status_code == 200 and "/login" not in str(response.url)
        except httpx.HTTPError:
            return False

    async def ensure_authenticated(self) -> None:
        """Ensure the session is authenticated."""
        if not self.is_authenticated:
            if await self._is_session_valid():
                self.is_authenticated = True
            else:
                await self.authenticate()

    async def get(self, url: str, **kwargs) -> httpx.Response:  # type: ignore
        """Make an authenticated GET request."""
        await self.ensure_authenticated()
        await self._apply_crawl_delay()
        return await self.client.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:  # type: ignore
        """Make an authenticated POST request."""
        await self.ensure_authenticated()
        await self._apply_crawl_delay()
        return await self.client.post(url, **kwargs)
