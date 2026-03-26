"""ContactImportHandler — CSV/JSON import for Person entities."""

import csv
import io
import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.person import create_person, update_person
from app.etl.base import BaseImportHandler
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate

# ── CSV header aliases ─────────────────────────────────────────────────────────

_ALIASES: dict[str, str] = {
    # first_name
    "first name": "first_name",
    "given_name": "first_name",
    "givenname": "first_name",
    "firstname": "first_name",
    # last_name
    "last name": "last_name",
    "family_name": "last_name",
    "surname": "last_name",
    "lastname": "last_name",
    # email
    "email address": "email",
    "e-mail": "email",
    # phone
    "mobile": "phone",
    "cell": "phone",
    "telephone": "phone",
    "phone number": "phone",
    # company
    "organization": "company",
    "org": "company",
    "employer": "company",
    # job_title
    "title": "job_title",
    "position": "job_title",
    # notes
    "note": "notes",
    "comments": "notes",
}

_CANONICAL = {
    "first_name",
    "last_name",
    "email",
    "phone",
    "company",
    "job_title",
    "notes",
}


def _normalise_header(h: str) -> str:
    key = h.strip().lower()
    return _ALIASES.get(key, key)


def _row_to_dict(raw_row: dict) -> dict:
    """Normalise header keys and keep only known canonical fields."""
    out: dict = {}
    for k, v in raw_row.items():
        canon = _normalise_header(k)
        if canon in _CANONICAL and v:
            out[canon] = v.strip()
    return out


class ContactImportHandler(BaseImportHandler):
    async def parse(self, raw_data: str, source_format: str) -> list[dict]:
        if source_format == "json":
            rows = json.loads(raw_data)
            return [_row_to_dict(r) for r in rows]

        # Default: CSV
        reader = csv.DictReader(io.StringIO(raw_data))
        return [_row_to_dict(dict(row)) for row in reader]

    async def find_candidates(
        self, db: AsyncSession, owner_id: uuid.UUID, row: dict
    ) -> list[dict]:
        email = row.get("email")
        phone = row.get("phone")
        first = row.get("first_name", "")
        last = row.get("last_name", "")

        stmt = select(Person).where(
            Person.owner_id == owner_id, Person.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        all_persons = result.scalars().all()

        candidates: list[dict] = []
        for p in all_persons:
            score = 0
            if email and p.email and p.email.lower() == email.lower():
                score += 10
            if phone and p.phone and p.phone == phone:
                score += 8
            if first and p.first_name and p.first_name.lower() == first.lower():
                score += 3
            if last and p.last_name and p.last_name.lower() == last.lower():
                score += 3
            if score >= 3:
                candidates.append(
                    {
                        "id": str(p.id),
                        "name": f"{p.first_name} {p.last_name or ''}".strip(),
                        "email": p.email,
                        "phone": p.phone,
                        "score": score,
                    }
                )

        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[:5]  # Cap at 5 candidates

    async def execute_create(
        self, db: AsyncSession, owner_id: uuid.UUID, row: dict
    ) -> uuid.UUID:
        data = PersonCreate(
            first_name=row.get("first_name", "Unknown"),
            last_name=row.get("last_name"),
            email=row.get("email"),
            phone=row.get("phone"),
            company=row.get("company"),
            job_title=row.get("job_title"),
            notes=row.get("notes"),
        )
        person = await create_person(db, owner_id, data)
        return person.id

    async def execute_merge(
        self, db: AsyncSession, owner_id: uuid.UUID, target_id: uuid.UUID, row: dict
    ) -> uuid.UUID:
        update_data: dict = {}
        for f in ("email", "phone", "company", "job_title", "notes"):
            if row.get(f):
                update_data[f] = row[f]
        if row.get("last_name"):
            update_data["last_name"] = row["last_name"]

        if update_data:
            data = PersonUpdate(**update_data)
            await update_person(db, target_id, owner_id, data)
        return target_id
