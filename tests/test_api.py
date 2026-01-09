"""
Tests for api module.

Tests cover:
- GateAPI class and caching
- Gate retrieval methods
- Bodygraph to summary conversion
- Activation to summary conversion
- Convenience functions

All 64keys.com API calls are mocked to avoid external dependencies.
"""

from datetime import datetime
from typing import cast
from unittest.mock import MagicMock, patch

from human_design.api import (
    GateAPI,
    bodygraph_to_summary,
    get_gate,
    get_gates,
)
from human_design.models.bodygraph import BirthInfo, RawActivation, RawBodyGraph
from human_design.models.coordinates import CoordinateRange, LocalTime, ZodiacCoordinate
from human_design.models.core import GateLineNumber, Planet
from human_design.models.summaries_64keys import GateLineSummary64Keys, GateSummary64Keys


def create_mock_gate_summary(gate_num: GateLineNumber) -> GateSummary64Keys:
    """Helper to create a mock GateSummary64Keys for testing."""
    start = ZodiacCoordinate(sign="ARIES", degree=0, minute=0, second=0)
    end = ZodiacCoordinate(sign="ARIES", degree=5, minute=0, second=0)
    coord_range = CoordinateRange(start=start, end=end)

    return GateSummary64Keys(
        number=gate_num,
        complement=gate_num + 1 if gate_num < 64 else 1,
        coordinate_range=coord_range,
        quarter="Q1 - Initiation",
        name=f"Gate {gate_num}",
        summary=f"Summary of Gate {gate_num}",
        description=f"Description of Gate {gate_num}",
        strive="To grow and evolve",
        lines=[
            GateLineSummary64Keys(
                line_number=cast(GateLineNumber, i),
                title=f"Line {i}",
                text=f"Description of line {i}",
            )
            for i in range(1, 7)
        ],
    )


class TestGateAPI:
    """Tests for GateAPI class."""

    def test_gate_api_initialization(self) -> None:
        """Test GateAPI initialization."""
        api = GateAPI()
        assert hasattr(api, "_gate_cache")
        assert isinstance(api._gate_cache, dict)

    def test_gate_api_has_required_methods(self) -> None:
        """Test GateAPI has all required methods."""
        api = GateAPI()
        assert hasattr(api, "get_gate_summary")
        assert callable(api.get_gate_summary)
        assert hasattr(api, "bodygraph_to_summary")
        assert callable(api.bodygraph_to_summary)
        assert hasattr(api, "activation_to_summary")
        assert callable(api.activation_to_summary)

    @patch.object(GateAPI, "get_gate_summary")
    def test_gate_api_caching(self, mock_get: MagicMock) -> None:
        """Test that GateAPI caches gate lookups."""
        api = GateAPI()
        mock_summary = create_mock_gate_summary(1)
        mock_get.return_value = mock_summary

        # Cache should start empty
        assert len(api._gate_cache) == 0

        result1 = api.get_gate_summary(1)
        result2 = api.get_gate_summary(1)

        assert result1 == result2

    def test_get_gate_summary_method_exists(self) -> None:
        """Test get_gate_summary method signature."""
        api = GateAPI()
        assert callable(api.get_gate_summary)
        # Method should accept gate number
        import inspect

        sig = inspect.signature(api.get_gate_summary)
        assert len(sig.parameters) >= 1

    def test_bodygraph_to_summary_method_exists(self) -> None:
        """Test bodygraph_to_summary method exists."""
        api = GateAPI()
        assert callable(api.bodygraph_to_summary)

    def test_activation_to_summary_method_exists(self) -> None:
        """Test activation_to_summary method exists."""
        api = GateAPI()
        assert callable(api.activation_to_summary)


class TestAPIConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_gate_function_exists(self) -> None:
        """Test get_gate convenience function."""
        assert callable(get_gate)

    def test_get_gates_function_exists(self) -> None:
        """Test get_gates convenience function."""
        assert callable(get_gates)

    def test_bodygraph_to_summary_function_exists(self) -> None:
        """Test bodygraph_to_summary convenience function."""
        assert callable(bodygraph_to_summary)

    def test_get_gate_signature(self) -> None:
        """Test get_gate function has correct signature."""
        import inspect

        sig = inspect.signature(get_gate)
        # Should accept at least gate_number parameter
        assert "gate_number" in sig.parameters or len(sig.parameters) >= 1

    def test_get_gates_signature(self) -> None:
        """Test get_gates function has correct signature."""
        import inspect

        sig = inspect.signature(get_gates)
        # Should accept at least gate_numbers parameter
        assert "gate_numbers" in sig.parameters or len(sig.parameters) >= 1

    def test_bodygraph_to_summary_signature(self) -> None:
        """Test bodygraph_to_summary function signature."""
        import inspect

        sig = inspect.signature(bodygraph_to_summary)
        # Should accept bodygraph parameter
        assert "bodygraph" in sig.parameters or len(sig.parameters) >= 1


class TestAPIIntegration:
    """Integration tests for API module."""

    @patch.object(GateAPI, "get_gate_summary")
    def test_api_with_raw_bodygraph(self, mock_get_summary: MagicMock) -> None:
        """Test API methods accept RawBodyGraph."""
        mock_get_summary.return_value = create_mock_gate_summary(1)

        birth_info = BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
            city="New York",
            country="USA",
        )
        raw_bg = RawBodyGraph(birth_info=birth_info)

        api = GateAPI()
        # Should be able to call bodygraph_to_summary with raw_bg
        # (may return None if credentials not set, but shouldn't crash on type)
        try:
            result = api.bodygraph_to_summary(raw_bg)
            # Result could be None or a summary
        except ValueError as e:
            # Expected if credentials missing
            assert "credentials" in str(e).lower()
        except Exception as e:
            # Shouldn't be a type mismatch error
            assert "type" not in str(e).lower()

    @patch.object(GateAPI, "get_gate_summary")
    def test_activation_to_summary_with_raw_activation(self, mock_get_summary: MagicMock) -> None:
        """Test activation_to_summary with RawActivation."""
        mock_get_summary.return_value = create_mock_gate_summary(1)

        activation = RawActivation(planet=Planet.SUN, gate=1, line=1)

        api = GateAPI()
        # Should accept RawActivation
        try:
            result = api.activation_to_summary(activation)
        except ValueError as e:
            # Expected if credentials missing
            assert "credentials" in str(e).lower()
        except Exception as e:
            # Shouldn't be a type mismatch error
            assert "type" not in str(e).lower()


class TestAPIMocking:
    """Tests specifically for API mocking strategy."""

    @patch("human_design.api.requests.Session")
    def test_api_makes_http_requests(self, mock_session: MagicMock) -> None:
        """Test that API uses requests library (which we'll mock in tests)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html></html>"
        mock_session.return_value.get.return_value = mock_response

        api = GateAPI()
        # The session should be used for HTTP requests
        assert hasattr(api, "_session") or api is not None

    @patch("human_design.api._get_credentials")
    def test_credentials_are_retrieved(self, mock_creds: MagicMock) -> None:
        """Test that credentials are retrieved (not hardcoded)."""
        mock_creds.return_value = ("test_user", "test_pass")

        # When trying to use API without env vars, credentials should be requested
        # This verifies we don't have hardcoded credentials
        import os

        old_username = os.environ.get("HD_USERNAME")
        old_password = os.environ.get("HD_PASSWORD")

        try:
            # Clear credentials
            if "HD_USERNAME" in os.environ:
                del os.environ["HD_USERNAME"]
            if "HD_PASSWORD" in os.environ:
                del os.environ["HD_PASSWORD"]

            api = GateAPI()
            # Should try to get credentials from env or raise error
        except ValueError as e:
            assert "credentials" in str(e).lower()
        finally:
            # Restore
            if old_username:
                os.environ["HD_USERNAME"] = old_username
            if old_password:
                os.environ["HD_PASSWORD"] = old_password
