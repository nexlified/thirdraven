import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.iso_reference import router as iso_router
from app.core.database import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.iso_reference import CountryPublic, LanguagePublic, TimezonePublic

OWNER_ID = uuid.uuid4()
COUNTRY_ID = uuid.uuid4()
LANGUAGE_ID = uuid.uuid4()
TIMEZONE_ID = uuid.uuid4()

FAKE_USER = User(
    id=OWNER_ID,
    username="testuser",
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    created_at=datetime.utcnow(),
)


def make_country(**kwargs) -> CountryPublic:
    defaults = dict(
        id=COUNTRY_ID,
        name="India",
        alpha2="IN",
        alpha3="IND",
        numeric="356",
        calling_code="+91",
        region="Asia",
        subregion="Southern Asia",
        flag_emoji="🇮🇳",
        is_active=True,
    )
    defaults.update(kwargs)
    return CountryPublic(**defaults)


def make_language(**kwargs) -> LanguagePublic:
    defaults = dict(
        id=LANGUAGE_ID,
        name="English",
        native_name="English",
        iso_639_1="en",
        iso_639_2="eng",
        is_active=True,
    )
    defaults.update(kwargs)
    return LanguagePublic(**defaults)


def make_timezone(**kwargs) -> TimezonePublic:
    defaults = dict(
        id=TIMEZONE_ID,
        name="Asia/Kolkata",
        utc_offset="+05:30",
        utc_offset_dst=None,
        country_id=COUNTRY_ID,
        is_active=True,
    )
    defaults.update(kwargs)
    return TimezonePublic(**defaults)


@pytest.fixture
def app_client():
    app = FastAPI()
    app.include_router(iso_router, prefix="/api/v1")

    fake_db = AsyncMock()

    async def override_get_session():
        yield fake_db

    async def override_get_current_user():
        return FAKE_USER

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ── GET /iso/countries/ ───────────────────────────────────────────────────────


def test_list_countries_returns_list(app_client):
    countries = [
        make_country(),
        make_country(
            id=uuid.uuid4(), name="USA", alpha2="US", alpha3="USA", numeric="840"
        ),
    ]
    with patch(
        "app.api.v1.iso_reference.list_countries",
        new=AsyncMock(return_value=countries),
    ):
        resp = app_client.get("/api/v1/iso/countries/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_countries_empty(app_client):
    with patch(
        "app.api.v1.iso_reference.list_countries",
        new=AsyncMock(return_value=[]),
    ):
        resp = app_client.get("/api/v1/iso/countries/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_countries_search_filter(app_client):
    with patch(
        "app.api.v1.iso_reference.list_countries",
        new=AsyncMock(return_value=[]),
    ) as mock_list:
        resp = app_client.get("/api/v1/iso/countries/?search=India")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["search"] == "India"


# ── GET /iso/countries/{alpha2} ───────────────────────────────────────────────


def test_get_country_found(app_client):
    country = make_country()
    with patch(
        "app.api.v1.iso_reference.get_country_by_alpha2",
        new=AsyncMock(return_value=country),
    ):
        resp = app_client.get("/api/v1/iso/countries/IN")
    assert resp.status_code == 200
    body = resp.json()
    assert body["alpha2"] == "IN"
    assert body["name"] == "India"


def test_get_country_not_found(app_client):
    with patch(
        "app.api.v1.iso_reference.get_country_by_alpha2",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get("/api/v1/iso/countries/XX")
    assert resp.status_code == 404


def test_get_country_fields(app_client):
    country = make_country()
    with patch(
        "app.api.v1.iso_reference.get_country_by_alpha2",
        new=AsyncMock(return_value=country),
    ):
        resp = app_client.get("/api/v1/iso/countries/IN")
    assert resp.status_code == 200
    body = resp.json()
    assert body["calling_code"] == "+91"
    assert body["region"] == "Asia"
    assert body["flag_emoji"] == "🇮🇳"


# ── GET /iso/languages/ ───────────────────────────────────────────────────────


def test_list_languages_returns_list(app_client):
    languages = [
        make_language(),
        make_language(
            id=uuid.uuid4(),
            name="Hindi",
            native_name="हिन्दी",
            iso_639_1="hi",
            iso_639_2="hin",
        ),
    ]
    with patch(
        "app.api.v1.iso_reference.list_languages",
        new=AsyncMock(return_value=languages),
    ):
        resp = app_client.get("/api/v1/iso/languages/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_languages_empty(app_client):
    with patch(
        "app.api.v1.iso_reference.list_languages",
        new=AsyncMock(return_value=[]),
    ):
        resp = app_client.get("/api/v1/iso/languages/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_languages_search_filter(app_client):
    with patch(
        "app.api.v1.iso_reference.list_languages",
        new=AsyncMock(return_value=[]),
    ) as mock_list:
        resp = app_client.get("/api/v1/iso/languages/?search=English")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["search"] == "English"


# ── GET /iso/languages/{iso_639_1} ────────────────────────────────────────────


def test_get_language_found(app_client):
    language = make_language()
    with patch(
        "app.api.v1.iso_reference.get_language_by_code",
        new=AsyncMock(return_value=language),
    ):
        resp = app_client.get("/api/v1/iso/languages/en")
    assert resp.status_code == 200
    body = resp.json()
    assert body["iso_639_1"] == "en"
    assert body["name"] == "English"


def test_get_language_not_found(app_client):
    with patch(
        "app.api.v1.iso_reference.get_language_by_code",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get("/api/v1/iso/languages/xx")
    assert resp.status_code == 404


# ── GET /iso/timezones/ ───────────────────────────────────────────────────────


def test_list_timezones_returns_list(app_client):
    timezones = [
        make_timezone(),
        make_timezone(
            id=uuid.uuid4(),
            name="UTC",
            utc_offset="+00:00",
            country_id=None,
        ),
    ]
    with patch(
        "app.api.v1.iso_reference.list_timezones",
        new=AsyncMock(return_value=timezones),
    ):
        resp = app_client.get("/api/v1/iso/timezones/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_timezones_empty(app_client):
    with patch(
        "app.api.v1.iso_reference.list_timezones",
        new=AsyncMock(return_value=[]),
    ):
        resp = app_client.get("/api/v1/iso/timezones/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_timezones_country_filter(app_client):
    with patch(
        "app.api.v1.iso_reference.list_timezones",
        new=AsyncMock(return_value=[]),
    ) as mock_list:
        resp = app_client.get("/api/v1/iso/timezones/?country=IN")
    assert resp.status_code == 200
    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["country_alpha2"] == "IN"


# ── GET /iso/timezones/{timezone_id} ──────────────────────────────────────────


def test_get_timezone_found(app_client):
    tz = make_timezone()
    with patch(
        "app.api.v1.iso_reference.get_timezone_by_id",
        new=AsyncMock(return_value=tz),
    ):
        resp = app_client.get(f"/api/v1/iso/timezones/{TIMEZONE_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Asia/Kolkata"
    assert body["utc_offset"] == "+05:30"


def test_get_timezone_not_found(app_client):
    with patch(
        "app.api.v1.iso_reference.get_timezone_by_id",
        new=AsyncMock(return_value=None),
    ):
        resp = app_client.get(f"/api/v1/iso/timezones/{uuid.uuid4()}")
    assert resp.status_code == 404
