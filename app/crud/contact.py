import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.contact import Contact
from app.models.relationship import ContactRelationship
from app.schemas.contact import ContactCreate, ContactUpdate


async def create_contact(
    db: AsyncSession, owner_id: uuid.UUID, data: ContactCreate
) -> Contact:
    contact = Contact(owner_id=owner_id, **data.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def get_contact(
    db: AsyncSession, contact_id: uuid.UUID, owner_id: uuid.UUID
) -> Contact | None:
    result = await db.exec(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.owner_id == owner_id,
            Contact.deleted_at.is_(None),
        )
    )
    return result.first()


async def list_contacts(
    db: AsyncSession, owner_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> list[Contact]:
    result = await db.exec(
        select(Contact)
        .where(Contact.owner_id == owner_id, Contact.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
    )
    return list(result.all())


async def update_contact(
    db: AsyncSession,
    contact_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ContactUpdate,
) -> Contact | None:
    contact = await get_contact(db, contact_id, owner_id)
    if not contact:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    contact.updated_at = datetime.utcnow()
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def soft_delete_contact(
    db: AsyncSession, contact_id: uuid.UUID, owner_id: uuid.UUID
) -> Contact | None:
    contact = await get_contact(db, contact_id, owner_id)
    if not contact:
        return None
    contact.deleted_at = datetime.utcnow()
    db.add(contact)
    await db.commit()
    return contact


async def add_relationship(
    db: AsyncSession,
    from_id: uuid.UUID,
    to_id: uuid.UUID,
    label: str,
    owner_id: uuid.UUID,
) -> ContactRelationship:
    rel = ContactRelationship(from_contact_id=from_id, to_contact_id=to_id, label=label)
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return rel


async def get_relationships_for_contact(
    db: AsyncSession, contact_id: uuid.UUID
) -> list[ContactRelationship]:
    result = await db.exec(
        select(ContactRelationship).where(
            ContactRelationship.from_contact_id == contact_id
        )
    )
    return list(result.all())
