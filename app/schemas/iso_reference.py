import uuid

from pydantic import BaseModel


class CountrySlim(BaseModel):
    id: uuid.UUID
    name: str
    alpha2: str

    model_config = {"from_attributes": True}


class CountryPublic(BaseModel):
    id: uuid.UUID
    name: str
    alpha2: str
    alpha3: str
    numeric: str
    calling_code: str | None
    region: str | None
    subregion: str | None
    flag_emoji: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class LanguageSlim(BaseModel):
    id: uuid.UUID
    name: str
    iso_639_1: str

    model_config = {"from_attributes": True}


class LanguagePublic(BaseModel):
    id: uuid.UUID
    name: str
    native_name: str
    iso_639_1: str
    iso_639_2: str
    is_active: bool

    model_config = {"from_attributes": True}


class TimezonePublic(BaseModel):
    id: uuid.UUID
    name: str
    utc_offset: str
    utc_offset_dst: str | None
    country_id: uuid.UUID | None
    is_active: bool

    model_config = {"from_attributes": True}
