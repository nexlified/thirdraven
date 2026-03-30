import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.crud.iso_reference import (
    get_country_by_alpha2,
    get_language_by_code,
    get_timezone_by_id,
    list_countries,
    list_languages,
    list_timezones,
)
from app.schemas.iso_reference import CountryPublic, LanguagePublic, TimezonePublic

router = APIRouter(prefix="/iso", tags=["iso-reference"])


# ── Countries ──────────────────────────────────────────────────────────────────


@router.get("/countries/", response_model=list[CountryPublic])
async def list_all_countries(
    db: Annotated[AsyncSession, Depends(get_session)],
    search: str | None = None,
    skip: int = 0,
    limit: int = 300,
):
    return await list_countries(db, skip=skip, limit=limit, search=search)


@router.get("/countries/{alpha2}", response_model=CountryPublic)
async def get_country(
    alpha2: str,
    db: Annotated[AsyncSession, Depends(get_session)]
):
    country = await get_country_by_alpha2(db, alpha2)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


# ── Languages ──────────────────────────────────────────────────────────────────


@router.get("/languages/", response_model=list[LanguagePublic])
async def list_all_languages(
    db: Annotated[AsyncSession, Depends(get_session)],
    search: str | None = None,
    skip: int = 0,
    limit: int = 200,
):
    return await list_languages(db, skip=skip, limit=limit, search=search)


@router.get("/languages/{iso_639_1}", response_model=LanguagePublic)
async def get_language(
    iso_639_1: str,
    db: Annotated[AsyncSession, Depends(get_session)]
):
    lang = await get_language_by_code(db, iso_639_1)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    return lang


# ── Timezones ──────────────────────────────────────────────────────────────────


@router.get("/timezones/", response_model=list[TimezonePublic])
async def list_all_timezones(
    db: Annotated[AsyncSession, Depends(get_session)],
    country: str | None = None,
    skip: int = 0,
    limit: int = 200,
):
    return await list_timezones(db, skip=skip, limit=limit, country_alpha2=country)


@router.get("/timezones/{timezone_id}", response_model=TimezonePublic)
async def get_timezone(
    timezone_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_session)]
):
    tz = await get_timezone_by_id(db, timezone_id)
    if not tz:
        raise HTTPException(status_code=404, detail="Timezone not found")
    return tz
