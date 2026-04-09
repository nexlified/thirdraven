"""
Integration tests for the vocabularies API.
Mirrors: frontend/src/api/vocabularies.ts
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/vocabularies"

# Use a custom vocabulary (not one of the seeded system vocabs) to avoid
# conflicts with locked/seeded data.
TEST_VOCAB = "test-custom-vocab"


async def test_list_vocabularies(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.get(f"{BASE}/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    # Seeded vocabularies should be present
    assert len(body) > 0
    first = body[0]
    assert "id" in first
    assert "machine_name" in first
    assert "name" in first


async def test_list_vocabularies_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"{BASE}/")
    assert resp.status_code == 401
    assert "detail" in resp.json()


async def test_create_vocabulary(api_client: AsyncClient, auth_headers: dict) -> None:
    resp = await api_client.post(
        f"{BASE}/",
        json={
            "name": "Test Custom Vocab",
            "machine_name": TEST_VOCAB,
            "description": "Integration test vocab",
            "is_hierarchical": False,
            "allows_new_terms": True,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["machine_name"] == TEST_VOCAB
    assert body["name"] == "Test Custom Vocab"
    assert "id" in body


async def test_get_vocabulary(api_client: AsyncClient, auth_headers: dict) -> None:
    # Create vocab first
    await api_client.post(
        f"{BASE}/",
        json={"name": "Get Vocab Test", "machine_name": "get-vocab-test"},
        headers=auth_headers,
    )
    resp = await api_client.get(f"{BASE}/get-vocab-test", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["machine_name"] == "get-vocab-test"


async def test_create_term(api_client: AsyncClient, auth_headers: dict) -> None:
    vocab_name = "terms-test-vocab"
    await api_client.post(
        f"{BASE}/",
        json={"name": "Terms Test Vocab", "machine_name": vocab_name},
        headers=auth_headers,
    )
    resp = await api_client.post(
        f"{BASE}/{vocab_name}/terms",
        json={"name": "Alpha Term", "slug": "alpha-term"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["slug"] == "alpha-term"
    assert body["name"] == "Alpha Term"
    assert "id" in body
    assert "vocabulary_id" in body


async def test_list_terms_for_seeded_vocab(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    resp = await api_client.get(
        f"{BASE}/asset-categories/terms", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) > 0
    slugs = [t["slug"] for t in body]
    assert "electronics" in slugs


async def test_update_term(api_client: AsyncClient, auth_headers: dict) -> None:
    vocab_name = "update-term-vocab"
    await api_client.post(
        f"{BASE}/",
        json={"name": "Update Term Vocab", "machine_name": vocab_name},
        headers=auth_headers,
    )
    await api_client.post(
        f"{BASE}/{vocab_name}/terms",
        json={"name": "Beta", "slug": "beta"},
        headers=auth_headers,
    )
    resp = await api_client.patch(
        f"{BASE}/{vocab_name}/terms/beta",
        json={"name": "Beta Updated"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Beta Updated"


async def test_delete_term_returns_204(
    api_client: AsyncClient, auth_headers: dict
) -> None:
    vocab_name = "delete-term-vocab"
    await api_client.post(
        f"{BASE}/",
        json={"name": "Delete Term Vocab", "machine_name": vocab_name},
        headers=auth_headers,
    )
    await api_client.post(
        f"{BASE}/{vocab_name}/terms",
        json={"name": "Gamma", "slug": "gamma"},
        headers=auth_headers,
    )
    resp = await api_client.delete(
        f"{BASE}/{vocab_name}/terms/gamma", headers=auth_headers
    )
    assert resp.status_code == 204
    assert resp.content == b""
