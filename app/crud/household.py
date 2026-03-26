import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.household import Household, HouseholdMember
from app.models.user import User
from app.schemas.household import (
    HouseholdCreate,
    HouseholdMemberPublic,
    HouseholdPublic,
)


# ── Shared helper ──────────────────────────────────────────────────────────────


async def get_user_household_id(
    db: AsyncSession, user_id: uuid.UUID
) -> uuid.UUID | None:
    """Return the household_id for a user, or None if not in any household."""
    r = await db.execute(
        select(HouseholdMember).where(HouseholdMember.user_id == user_id)
    )
    member = r.scalars().first()
    return member.household_id if member else None


# ── Internal builders ──────────────────────────────────────────────────────────


async def _build_member_public(
    db: AsyncSession, member: HouseholdMember
) -> HouseholdMemberPublic:
    r = await db.execute(select(User).where(User.id == member.user_id))
    user = r.scalars().first()
    return HouseholdMemberPublic(
        id=member.id,
        user_id=member.user_id,
        username=user.username if user else "",
        role=member.role,
        joined_at=member.joined_at,
    )


async def _build_household_public(
    db: AsyncSession, household: Household
) -> HouseholdPublic:
    r = await db.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household.id
        )
    )
    members_raw = r.scalars().all()
    members = [await _build_member_public(db, m) for m in members_raw]
    return HouseholdPublic(
        id=household.id,
        name=household.name,
        created_by=household.created_by,
        members=members,
        created_at=household.created_at,
    )


# ── Revert helpers ─────────────────────────────────────────────────────────────


async def _revert_user_household_records(
    db: AsyncSession, user_id: uuid.UUID, household_id: uuid.UUID
) -> None:
    """Bulk-revert all records owned by user_id that were shared with household_id.
    Must be called within an open transaction; commit is the caller's responsibility.
    """
    from app.models.organization import Organization
    from app.models.person import Person

    await db.execute(
        update(Person)
        .where(Person.owner_id == user_id, Person.household_id == household_id)
        .values(visibility="private", household_id=None)
    )
    await db.execute(
        update(Organization)
        .where(
            Organization.owner_id == user_id,
            Organization.household_id == household_id,
        )
        .values(visibility="private", household_id=None)
    )


async def _disband_household(db: AsyncSession, household_id: uuid.UUID) -> None:
    """Revert all shared records, delete all members, delete the household."""
    from app.models.organization import Organization
    from app.models.person import Person

    await db.execute(
        update(Person)
        .where(Person.household_id == household_id)
        .values(visibility="private", household_id=None)
    )
    await db.execute(
        update(Organization)
        .where(Organization.household_id == household_id)
        .values(visibility="private", household_id=None)
    )
    await db.execute(
        delete(HouseholdMember).where(HouseholdMember.household_id == household_id)
    )
    r = await db.execute(select(Household).where(Household.id == household_id))
    household = r.scalars().first()
    if household:
        await db.delete(household)
    await db.commit()


# ── CRUD ──────────────────────────────────────────────────────────────────────


async def create_household(
    db: AsyncSession, user_id: uuid.UUID, data: HouseholdCreate
) -> HouseholdPublic:
    existing = await get_user_household_id(db, user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of a household.",
        )
    household = Household(name=data.name, created_by=user_id)
    db.add(household)
    await db.flush()
    admin_member = HouseholdMember(
        household_id=household.id, user_id=user_id, role="admin"
    )
    db.add(admin_member)
    await db.commit()
    await db.refresh(household)
    return await _build_household_public(db, household)


async def get_my_household(
    db: AsyncSession, user_id: uuid.UUID
) -> HouseholdPublic | None:
    household_id = await get_user_household_id(db, user_id)
    if not household_id:
        return None
    r = await db.execute(select(Household).where(Household.id == household_id))
    household = r.scalars().first()
    if not household:
        return None
    return await _build_household_public(db, household)


async def invite_member(
    db: AsyncSession,
    household_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
    username: str,
) -> HouseholdPublic:
    # Verify requester is admin of this household
    r = await db.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == requesting_user_id,
        )
    )
    requester_member = r.scalars().first()
    if not requester_member or requester_member.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admins only."
        )

    r = await db.execute(select(User).where(User.username == username))
    invitee = r.scalars().first()
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    existing = await get_user_household_id(db, invitee.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of a household.",
        )

    new_member = HouseholdMember(
        household_id=household_id, user_id=invitee.id, role="member"
    )
    db.add(new_member)
    await db.commit()

    r = await db.execute(select(Household).where(Household.id == household_id))
    household = r.scalars().first()
    return await _build_household_public(db, household)


async def remove_member(
    db: AsyncSession,
    household_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
    target_user_id: uuid.UUID,
) -> HouseholdPublic:
    r = await db.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == requesting_user_id,
        )
    )
    requester_member = r.scalars().first()
    if not requester_member or requester_member.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admins only."
        )

    if target_user_id == requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the leave endpoint to remove yourself.",
        )

    r = await db.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == target_user_id,
        )
    )
    target_member = r.scalars().first()
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found."
        )

    await db.delete(target_member)
    await _revert_user_household_records(db, target_user_id, household_id)
    await db.commit()

    r = await db.execute(select(Household).where(Household.id == household_id))
    household = r.scalars().first()
    return await _build_household_public(db, household)


async def leave_household(db: AsyncSession, user_id: uuid.UUID) -> None:
    household_id = await get_user_household_id(db, user_id)
    if not household_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not in a household.",
        )

    # Check if this user is the last admin with other members still present
    r = await db.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.role == "admin",
        )
    )
    admins = r.scalars().all()

    r2 = await db.execute(
        select(HouseholdMember).where(HouseholdMember.household_id == household_id)
    )
    all_members = r2.scalars().all()

    if len(admins) == 1 and admins[0].user_id == user_id:
        if len(all_members) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer admin role to another member before leaving.",
            )
        # Sole remaining member — disband the household
        await _disband_household(db, household_id)
        return

    r = await db.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == user_id,
        )
    )
    member = r.scalars().first()
    await db.delete(member)
    await _revert_user_household_records(db, user_id, household_id)
    await db.commit()
