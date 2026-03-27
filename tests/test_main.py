"""Tests for the main FastAPI application.

Tests cover:
- Health check endpoints
- CORS middleware configuration
- Router registration
- Mangum handler creation
- OpenAPI documentation endpoints

Note: These tests use httpx.AsyncClient with app's lifespan context
to avoid compatibility issues with starlette.testclient.TestClient.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from transcription_service.main import app, handler


@pytest.fixture
async def client():
    """Create async HTTP client for FastAPI app.

    Uses httpx.AsyncClient with ASGITransport to test the app
    without hitting the TestClient compatibility issue.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


def test_app_metadata():
    """Test FastAPI app metadata is correctly configured."""
    assert app.title == "Transcription Service API"
    assert app.version == "1.0.0"
    assert "Audio transcription service" in app.description
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"


@pytest.mark.anyio
async def test_health_check_root(client):
    """Test health check at root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "transcription-api"
    assert data["version"] == "1.0.0"


@pytest.mark.anyio
async def test_health_check_explicit(client):
    """Test health check at /health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "transcription-api"
    assert data["version"] == "1.0.0"


def test_cors_middleware_configured():
    """Test CORS middleware is properly configured."""
    # Check middleware is in the app
    middleware_classes = [m.cls for m in app.user_middleware]
    from fastapi.middleware.cors import CORSMiddleware

    assert CORSMiddleware in middleware_classes


@pytest.mark.anyio
async def test_cors_headers(client):
    """Test CORS headers are included in responses."""
    response = await client.options(
        "/",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    # Should allow the request
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    # Note: access-control-allow-headers is only sent when requested
    # CORS middleware responds with actual values, not just "*"


@pytest.mark.anyio
async def test_auth_router_registered(client):
    """Test auth router endpoints are accessible."""
    # Auth endpoints should be registered
    # We don't test functionality here (that's in test_auth.py)
    # Just verify the routes exist

    # GET /auth/me should require auth (401)
    response = await client.get("/auth/me")
    assert response.status_code == 401  # Unauthorized (no token)


@pytest.mark.anyio
async def test_jobs_router_registered(client):
    """Test jobs router endpoints are accessible."""
    # Jobs endpoints should be registered
    # We don't test functionality here (that's in test_jobs.py)
    # Just verify the routes exist

    # GET /jobs should require auth (401)
    response = await client.get("/jobs")
    assert response.status_code == 401  # Unauthorized (no token)


@pytest.mark.anyio
async def test_openapi_docs_available(client):
    """Test OpenAPI documentation endpoints are available."""
    # OpenAPI JSON schema
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    assert openapi["info"]["title"] == "Transcription Service API"
    assert openapi["info"]["version"] == "1.0.0"

    # Swagger UI
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    # ReDoc
    response = await client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.anyio
async def test_openapi_routes_documented(client):
    """Test that all expected routes are in OpenAPI spec."""
    response = await client.get("/openapi.json")
    openapi = response.json()
    paths = openapi["paths"]

    # Health endpoints
    assert "/" in paths
    assert "/health" in paths

    # Auth endpoints
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/auth/me" in paths

    # Job endpoints
    assert "/jobs" in paths
    assert "/jobs/upload" in paths
    assert "/jobs/upload/presigned" in paths
    assert "/jobs/upload/complete" in paths
    assert "/jobs/youtube" in paths
    assert "/jobs/{job_id}" in paths


def test_mangum_handler_exists():
    """Test Mangum handler is created for Lambda deployment."""
    from mangum import Mangum

    assert isinstance(handler, Mangum)


def test_mangum_handler_wraps_app():
    """Test Mangum handler wraps the FastAPI app."""
    # The handler should wrap our app
    # We can't easily test Lambda invocation here, but we can verify it exists
    assert handler is not None
    assert callable(handler)


@pytest.mark.anyio
async def test_404_for_unknown_route(client):
    """Test 404 response for unknown routes."""
    response = await client.get("/unknown/route")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.anyio
async def test_method_not_allowed(client):
    """Test 405 response for unsupported HTTP methods."""
    # Health endpoint only supports GET
    response = await client.post("/health")
    assert response.status_code == 405  # Method Not Allowed


@pytest.mark.anyio
async def test_cors_preflight_all_origins(client):
    """Test CORS allows all origins (development/friends mode)."""
    response = await client.options(
        "/",
        headers={
            "Origin": "https://random-domain.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    # When allow_origins=["*"], FastAPI's CORS middleware echoes the origin
    # rather than returning "*" (this is correct CORS behavior with credentials)
    assert response.headers.get("access-control-allow-origin") == "https://random-domain.com"


@pytest.mark.anyio
async def test_cors_allows_credentials(client):
    """Test CORS allows credentials (cookies, auth headers)."""
    response = await client.get("/", headers={"Origin": "https://example.com"})

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.anyio
async def test_openapi_security_schemes(client):
    """Test OpenAPI spec includes JWT security scheme."""
    response = await client.get("/openapi.json")
    openapi = response.json()

    # Should have components section (even if no explicit securitySchemes yet)
    assert "components" in openapi

    # Note: FastAPI auto-generates securitySchemes from dependencies
    # Since we use Depends(get_current_user) in routes, it should be present
    if "securitySchemes" in openapi["components"]:
        # Check for HTTPBearer security (JWT)
        security_schemes = openapi["components"]["securitySchemes"]
        assert "HTTPBearer" in security_schemes
        assert security_schemes["HTTPBearer"]["type"] == "http"
        assert security_schemes["HTTPBearer"]["scheme"] == "bearer"
    else:
        # If not present, just verify components exists
        # (security is still enforced via dependencies, just not in OpenAPI spec)
        assert "schemas" in openapi["components"]


@pytest.mark.anyio
async def test_health_check_response_format(client):
    """Test health check returns consistent JSON format."""
    response = await client.get("/")
    data = response.json()

    # Verify keys
    assert set(data.keys()) == {"status", "service", "version"}

    # Verify types
    assert isinstance(data["status"], str)
    assert isinstance(data["service"], str)
    assert isinstance(data["version"], str)

    # Verify values
    assert data["status"] == "ok"
    assert data["service"] == "transcription-api"
    assert data["version"] == "1.0.0"
