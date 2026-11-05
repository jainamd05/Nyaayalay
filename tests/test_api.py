import app.api.routes.analysis as analysis_route
import httpx
import openai
import pytest
from app.core.config import Settings
from app.main import app
from fastapi.testclient import TestClient

ORIGIN = "http://localhost:5173"
INCIDENT = {"incident": "Someone snatched my phone on the street and ran away."}


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_frontend_url_trailing_slash_and_lists_are_normalised():
    settings = Settings(frontend_url="https://nyaayalay.vercel.app/, https://example.com//")
    assert "https://nyaayalay.vercel.app" in settings.cors_origins
    assert "https://example.com" in settings.cors_origins
    assert "http://localhost:5173" in settings.cors_origins


def test_cors_preflight_allows_local_frontend(client):
    response = client.options(
        "/api/analysis",
        headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN


def _request():
    return httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (lambda: openai.APIConnectionError(request=_request()), 503),
        (lambda: openai.RateLimitError("slow down", response=httpx.Response(429, request=_request()), body=None), 429),
        (lambda: openai.AuthenticationError("bad key", response=httpx.Response(401, request=_request()), body=None), 503),
        (lambda: ValueError("boom"), 500),
    ],
)
def test_failures_return_json_detail_with_cors_headers(client, monkeypatch, error, status):
    def fail(_incident):
        raise error()

    monkeypatch.setattr(analysis_route, "analyze", fail)
    response = client.post("/api/analysis", json=INCIDENT, headers={"Origin": ORIGIN})
    assert response.status_code == status
    assert isinstance(response.json()["detail"], str)
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_missing_api_key_is_reported(client, monkeypatch):
    from nyayalay import llm

    monkeypatch.setattr(llm, "GROQ_API_KEY", "")
    response = client.post("/api/analysis", json=INCIDENT, headers={"Origin": ORIGIN})
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]


def test_short_incident_is_rejected(client):
    response = client.post("/api/analysis", json={"incident": "hi"})
    assert response.status_code == 422
