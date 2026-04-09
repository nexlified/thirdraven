"""
Integration tests for ISO reference data endpoints.
Mirrors: frontend/src/api/reference.ts

These endpoints have no auth requirement — they are public read-only.
Data is seeded into the test DB by the api_engine fixture (via seed_all).
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

ISO = "/api/v1/iso"


async def test_list_countries(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{ISO}/countries/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) > 0
    # Verify shape of first item
    first = body[0]
    assert "alpha2" in first
    assert "name" in first


async def test_get_country_by_alpha2(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{ISO}/countries/IN")
    assert resp.status_code == 200
    body = resp.json()
    assert body["alpha2"] == "IN"
    assert "name" in body
    assert "calling_code" in body


async def test_get_country_not_found(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{ISO}/countries/XX")
    assert resp.status_code == 404
    assert "detail" in resp.json()


async def test_list_languages(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{ISO}/languages/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) > 0
    first = body[0]
    assert "iso_639_1" in first
    assert "name" in first


async def test_get_language_by_code(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{ISO}/languages/en")
    assert resp.status_code == 200
    body = resp.json()
    assert body["iso_639_1"] == "en"
    assert "name" in body


async def test_list_timezones(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{ISO}/timezones/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) > 0
    first = body[0]
    assert "name" in first
    assert "id" in first
