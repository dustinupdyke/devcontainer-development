"""Integration tests for the HTTP API using FastAPI's TestClient."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from app.main import app, store
from fastapi import status
from fastapi.testclient import TestClient

VALID_URL = "https://www.example.com/very/long/path?ref=news"


@pytest.fixture(autouse=True)
def _reset_store() -> Iterator[None]:
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "ok"
    assert body["links"] == 0


def test_shorten_returns_created(client: TestClient) -> None:
    response = client.post("/shorten", json={"url": VALID_URL})
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["code"] == "1"
    assert body["target_url"].startswith("https://www.example.com/very/long/path")
    assert body["short_url"].endswith("/1")


@pytest.mark.parametrize(
    "bad_url",
    ["not-a-url", "example.com", "ftp://example.com", "javascript:alert(1)", ""],
)
def test_shorten_rejects_invalid_url(client: TestClient, bad_url: str) -> None:
    response = client.post("/shorten", json={"url": bad_url})
    assert response.status_code == 422


def test_shorten_rejects_missing_field(client: TestClient) -> None:
    response = client.post("/shorten", json={})
    assert response.status_code == 422


def test_shorten_is_idempotent_per_url(client: TestClient) -> None:
    first = client.post("/shorten", json={"url": VALID_URL}).json()
    second = client.post("/shorten", json={"url": VALID_URL}).json()
    assert first["code"] == second["code"]
    assert client.get("/health").json()["links"] == 1


def test_redirect_is_307_with_location(client: TestClient) -> None:
    code = client.post("/shorten", json={"url": VALID_URL}).json()["code"]
    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"].startswith("https://www.example.com/very/long/path")


def test_redirect_unknown_code_returns_404(client: TestClient) -> None:
    response = client.get("/doesnotexist", follow_redirects=False)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_stats_reports_and_counts_hits(client: TestClient) -> None:
    code = client.post("/shorten", json={"url": VALID_URL}).json()["code"]
    for _ in range(3):
        client.get(f"/{code}", follow_redirects=False)
    response = client.get(f"/stats/{code}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["code"] == code
    assert body["hits"] == 3
    assert body["target_url"].startswith("https://www.example.com/very/long/path")
    assert "created_at" in body


def test_stats_unknown_code_returns_404(client: TestClient) -> None:
    response = client.get("/stats/doesnotexist")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_stats_starts_at_zero_hits(client: TestClient) -> None:
    code = client.post("/shorten", json={"url": VALID_URL}).json()["code"]
    assert client.get(f"/stats/{code}").json()["hits"] == 0


def test_openapi_schema_is_available(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "URL Shortener"
    assert "/shorten" in schema["paths"]
