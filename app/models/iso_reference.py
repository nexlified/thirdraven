import uuid

from sqlmodel import Field, SQLModel


class Country(SQLModel, table=True):
    __tablename__ = "country"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    alpha2: str = Field(index=True, unique=True)
    alpha3: str = Field(index=True, unique=True)
    numeric: str
    calling_code: str | None = None
    region: str | None = None
    subregion: str | None = None
    flag_emoji: str | None = None
    is_active: bool = Field(default=True)


class Language(SQLModel, table=True):
    __tablename__ = "language"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    native_name: str
    iso_639_1: str = Field(index=True, unique=True)
    iso_639_2: str = Field(index=True, unique=True)
    is_active: bool = Field(default=True)


class Timezone(SQLModel, table=True):
    __tablename__ = "timezone"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
    utc_offset: str
    utc_offset_dst: str | None = None
    country_id: uuid.UUID | None = Field(default=None, foreign_key="country.id")
    is_active: bool = Field(default=True)
