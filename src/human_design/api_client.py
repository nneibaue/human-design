"""
64keys.com API Client

This module provides the core API functionality for fetching and validating
Human Design gate data from 64keys.com. It handles authentication and data
parsing, returning validated Pydantic models.

Key functionality:
- Authenticate with 64keys.com
- Fetch gate summaries with full descriptions
- Convert a RawBodyGraph to a BodyGraphSummary64Keys
"""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import boto3
import requests
from bs4 import BeautifulSoup

from .models import (
    ActivationSummary64Keys,
    BodyGraphDefinition,
    BodyGraphSummary64Keys,
    GateLineSummary64Keys,
    GateNumber,
    GateSummary64Keys,
    RawActivation,
    RawBodyGraph,
)


@lru_cache(maxsize=1)
def _get_credentials() -> tuple[str, str]:
    """
    Get credentials from AWS Secrets Manager or environment variables.

    Tries AWS Secrets Manager first (when SECRET_NAME env var is set),
    then falls back to environment variables for local development.

    Returns:
        Tuple of (username, password)

    Raises:
        ValueError: If credentials are not set in environment or Secrets Manager
    """
    # Try AWS Secrets Manager first (when deployed)
    secret_name = os.environ.get("SECRET_NAME")

    if secret_name:
        try:
            import boto3

            client = boto3.client("secretsmanager")
            response = client.get_secret_value(SecretId=secret_name)
            secrets = json.loads(response["SecretString"])
            return secrets["HD_USERNAME"], secrets["HD_PASSWORD"]
        except Exception as e:
            print(f"Warning: Failed to fetch from Secrets Manager: {e}")
            print("Falling back to environment variables")

    # Fallback to environment variables (local development)
    username = os.environ.get("HD_USERNAME")
    password = os.environ.get("HD_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Missing credentials. Set HD_USERNAME/HD_PASSWORD env vars "
            "or configure SECRET_NAME to use AWS Secrets Manager."
        )

    return username, password


def _load_cached_cookies() -> dict[str, str] | None:
    """
    Load cached session cookies from S3 or local disk.

    Returns:
        Dictionary of cookies if cache exists, None otherwise
    """
    data_bucket = os.environ.get("DATA_BUCKET")

    # Try S3 first if bucket is configured
    if data_bucket:
        try:
            s3 = boto3.client("s3")
            response = s3.get_object(Bucket=data_bucket, Key="session-cache.json")
            return json.loads(response["Body"].read())  # type: ignore
        except Exception:
            pass  # Fall through to local disk cache

    # Fall back to local disk cache for development
    config_dir = Path.home() / ".config" / "human-design"
    cache_path = config_dir / "session.json"
    if cache_path.exists():
        try:
            with open(cache_path) as f:
                return json.load(f)  # type: ignore
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _save_cookies(cookies: Any) -> None:
    """Save session cookies to S3 or local disk."""
    data_bucket = os.environ.get("DATA_BUCKET")
    cookies_dict = requests.utils.dict_from_cookiejar(cookies)

    # Try S3 first if bucket is configured
    if data_bucket:
        try:
            s3 = boto3.client("s3")
            s3.put_object(
                Bucket=data_bucket,
                Key="session-cache.json",
                Body=json.dumps(cookies_dict),
                ContentType="application/json",
            )
            return
        except Exception:
            pass  # Fall through to local disk cache

    # Fall back to local disk cache for development
    config_dir = Path.home() / ".config" / "human-design"
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_dir / "session.json", "w") as f:
            json.dump(cookies_dict, f)
    except OSError:
        pass  # Silently fail if we can't save cookies


class GateAPI:
    """
    Client for 64keys.com API with authentication and data validation.

    Usage:
        api = GateAPI()

        # Get a single gate summary
        gate = api.get_gate_summary(11)

        # Convert a raw bodygraph to full summary
        raw = RawBodyGraph(birth_info=...)
        summary = api.bodygraph_to_summary(raw)
    """

    BASE_URL = "https://www.64keys.com"
    LOGIN_URL = f"{BASE_URL}/login"
    HOME_URL = f"{BASE_URL}/main"
    LIBRARY_API_URL = f"{BASE_URL}/library_api"

    def __init__(self) -> None:
        """Initialize the API client."""
        self.is_authenticated = False
        self.session = requests.Session()

        # Cache for gate summaries to avoid redundant API calls
        self._gate_cache: dict[int, GateSummary64Keys] = {}

        # Try to load cached cookies
        cached_cookies = _load_cached_cookies()
        if cached_cookies:
            self.session.cookies.update(cached_cookies)

    def authenticate(self) -> None:
        """
        Authenticate with 64keys.com.

        Raises:
            ValueError: If credentials are not set
            requests.RequestException: If authentication fails
        """
        username, password = _get_credentials()

        # Get login page to grab CSRF token
        login_page = self.session.get(self.LOGIN_URL)
        soup = BeautifulSoup(login_page.text, "html.parser")
        csrf_token = soup.find("meta", {"name": "csrf-token"})["content"]  # type: ignore

        # Login with CSRF token
        login_data = {"name": username, "password": password, "remember": "on"}
        response = self.session.post(
            self.LOGIN_URL,
            data=login_data,
            headers={"X-CSRF-TOKEN": csrf_token},  # type: ignore
        )

        if response.status_code != 200:
            raise requests.RequestException(
                f"Authentication failed with status code {response.status_code}"
            )

        # Save cookies for future use
        _save_cookies(self.session.cookies)
        self.is_authenticated = True

    def _is_session_valid(self) -> bool:
        """
        Check if the cached session is still valid.

        Returns:
            True if session is valid, False otherwise
        """
        if not self.session.cookies:
            return False

        try:
            # Make a quick request to check if session is still valid
            response = self.session.get(self.HOME_URL, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _ensure_authenticated(self) -> None:
        """Ensure the session is authenticated."""
        if not self.is_authenticated:
            # Check if cached session is still valid
            if self._is_session_valid():
                self.is_authenticated = True
            else:
                self.authenticate()

    def _parse_gate_html(self, html: str) -> GateSummary64Keys:
        """
        Parse Gate HTML from API response and return validated Gate model.

        Args:
            html: HTML content from the API response
            gate_def: Optional gate definition to use for base fields

        Returns:
            Validated GateSummary64Keys model instance
        """
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find("div", {"id": "aspectscontainer"})

        if not container:
            raise ValueError("Could not find gate container in response")

        # Extract basic info
        gate_num_elem = container.find("div", {"class": "gatenumber"})  # type: ignore
        name_elem = container.find("div", {"class": "gatesubline"})  # type: ignore
        quarter_elem = container.find("div", {"class": "qinfo"})  # type: ignore
        summary_elem = container.find("div", {"class": "gatetext"})  # type: ignore

        if not all([gate_num_elem, name_elem, quarter_elem, summary_elem]):
            raise ValueError("Missing required gate information in response")

        gate_number = int(gate_num_elem.text.strip().replace("Gate ", ""))  # type: ignore
        name = name_elem.text.strip()  # type: ignore
        quarter = quarter_elem.text.strip().replace("Quarter: ", "")  # type: ignore
        summary = summary_elem.text.strip()  # type: ignore

        # Extract description
        description_elems = container.find_all("div", {"class": "potentialgatetext"})  # type: ignore
        description = description_elems[0].text.strip() if description_elems else ""

        # Extract strive
        strive_headline_tags = container.find_all(  # type: ignore
            "div", {"class": "potentialgateheadline"}
        )
        strive = ""
        for tag in strive_headline_tags:
            if "Strive" in tag.text:
                strive_text = tag.find_next("div", {"class": "gatetext"})
                strive = strive_text.text.strip() if strive_text else ""
                break

        # Extract lines
        lines = []
        line_headlines = container.find_all("div", {"class": "potentialgateheadline"})  # type: ignore

        for headline in line_headlines:
            line_text = headline.text.strip()
            # Check if this is a line number (e.g., "11.1")
            if "." in line_text and line_text[0].isdigit():
                try:
                    # Extract the fractional part as line number (1-6)
                    line_number_str = line_text.strip().split(".")[1]
                    line_number = int(line_number_str)
                    if not 1 <= line_number <= 6:
                        continue

                    # Get title (next gatesubline)
                    title_elem = headline.find_next("div", {"class": "gatesubline"})
                    title = title_elem.text.strip() if title_elem else ""

                    # Get text (next gatetext)
                    text_elem = title_elem.find_next("div", {"class": "gatetext"})
                    text = text_elem.text.strip() if text_elem else ""

                    lines.append(
                        GateLineSummary64Keys(line_number=line_number, title=title, text=text)  # type: ignore
                    )
                except (ValueError, AttributeError, IndexError):
                    continue

        # Get gate definition from bodygraph for coordinate_range and bridge
        bodygraph_def = BodyGraphDefinition.load()
        gate_def_from_bodygraph = bodygraph_def.get_gate(gate_number)

        if gate_def_from_bodygraph is None:
            raise ValueError(f"Gate {gate_number} not found in bodygraph definition")

        return GateSummary64Keys(
            number=gate_number,  # type: ignore
            complement=gate_def_from_bodygraph.complement,
            coordinate_range=gate_def_from_bodygraph.coordinate_range,
            quarter=quarter,
            name=name,
            summary=summary,
            description=description,
            strive=strive,
            lines=lines,
        )

    def get_gate_summary(self, gate_number: int) -> GateSummary64Keys:
        """
        Fetch a Gate definition and return validated Gate model.

        Uses caching to avoid redundant API calls for the same gate.

        Args:
            gate_number: Gate number (1-64)

        Returns:
            Validated GateSummary64Keys model instance

        Raises:
            ValueError: If gate_number is invalid
            requests.RequestException: If API request fails
        """
        if not 1 <= gate_number <= 64:
            raise ValueError(f"Gate number must be between 1 and 64, got {gate_number}")

        # Check cache first
        if gate_number in self._gate_cache:
            return self._gate_cache[gate_number]

        self._ensure_authenticated()

        response = self.session.get(
            self.LIBRARY_API_URL,
            params={"type": "gate", "param1": str(gate_number)},
        )

        if response.status_code != 200:
            raise requests.RequestException(
                f"Failed to fetch gate {gate_number} (Status: {response.status_code})"
            )

        gate = self._parse_gate_html(response.text)

        # Cache the result
        self._gate_cache[gate_number] = gate

        return gate

    def activation_to_summary(self, raw: RawActivation) -> ActivationSummary64Keys:
        """
        Convert a RawActivation to an ActivationSummary64Keys.

        Fetches the gate summary from 64keys.com and combines with the raw activation.

        Args:
            raw: RawActivation with planet, gate, and line

        Returns:
            ActivationSummary64Keys with full gate and line summaries

        Raises:
            ValueError: If gate or line cannot be found
        """
        gate_summary = self.get_gate_summary(raw.gate)
        return ActivationSummary64Keys.from_raw(raw, gate_summary)

    def bodygraph_to_summary(self, raw_bodygraph: RawBodyGraph) -> BodyGraphSummary64Keys:
        """
        Convert a RawBodyGraph to a BodyGraphSummary64Keys.

        This is the main method for getting a complete bodygraph with full
        64keys content. It:
        1. Gets all unique gates from the raw bodygraph
        2. Fetches summaries for each gate from 64keys.com
        3. Converts each activation to include full content
        4. Returns the complete summary

        Args:
            raw_bodygraph: The calculated raw bodygraph

        Returns:
            BodyGraphSummary64Keys with full 64keys content
        """
        # Get all unique gates and fetch their summaries
        all_gate_numbers = list(raw_bodygraph.all_activated_gates)
        gate_summaries: dict[int, GateSummary64Keys] = {}
        for gate_num in all_gate_numbers:
            gate_summaries[gate_num] = self.get_gate_summary(gate_num)

        # Convert conscious activations
        conscious_summaries: list[ActivationSummary64Keys] = []
        for raw_act in raw_bodygraph.conscious_activations:
            gate_summary = gate_summaries[raw_act.gate]
            conscious_summaries.append(ActivationSummary64Keys.from_raw(raw_act, gate_summary))

        # Convert unconscious activations
        unconscious_summaries: list[ActivationSummary64Keys] = []
        for raw_act in raw_bodygraph.unconscious_activations:
            gate_summary = gate_summaries[raw_act.gate]
            unconscious_summaries.append(ActivationSummary64Keys.from_raw(raw_act, gate_summary))

        return BodyGraphSummary64Keys(
            birth_info_date=raw_bodygraph.birth_info.date,
            birth_info_city=raw_bodygraph.birth_info.city,
            birth_info_country=raw_bodygraph.birth_info.country,
            conscious_activations=conscious_summaries,
            unconscious_activations=unconscious_summaries,
        )

    def get_home_page(self) -> str:
        """
        Fetch the 64keys homepage.

        Returns:
            HTML content of the homepage

        Raises:
            requests.RequestException: If request fails
        """
        self._ensure_authenticated()

        response = self.session.get(self.HOME_URL)

        if response.status_code != 200:
            raise requests.RequestException(
                f"Failed to fetch homepage (Status: {response.status_code})"
            )

        return response.text


# Convenience functions for quick access
_api_instance: GateAPI | None = None


def _get_api() -> GateAPI:
    """Get or create the singleton API instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = GateAPI()
    return _api_instance


def get_gate(gate_number: int) -> GateSummary64Keys:
    """
    Convenience function to fetch a Gate.

    Args:
        gate_number: Gate number (1-64)

    Returns:
        Validated GateSummary64Keys model instance
    """
    return _get_api().get_gate_summary(gate_number)


def get_gates(gate_numbers: list[GateNumber]) -> dict[int, GateSummary64Keys]:
    """
    Convenience function to fetch multiple Gates.

    Args:
        gate_numbers: List of gate numbers (1-64)

    Returns:
        Dictionary mapping gate number to GateSummary64Keys
    """
    api = _get_api()
    result: dict[int, GateSummary64Keys] = {}
    for gate_num in gate_numbers:
        result[gate_num] = api.get_gate_summary(gate_num)
    return result


def bodygraph_to_summary(raw_bodygraph: RawBodyGraph) -> BodyGraphSummary64Keys:
    """
    Convenience function to convert a RawBodyGraph to a BodyGraphSummary64Keys.

    Args:
        raw_bodygraph: The calculated raw bodygraph

    Returns:
        BodyGraphSummary64Keys with full 64keys content
    """
    return _get_api().bodygraph_to_summary(raw_bodygraph)


def get_home_page() -> str:
    """
    Convenience function to fetch the homepage.

    Returns:
        HTML content of the homepage
    """
    return _get_api().get_home_page()
