import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import hash_password
from app.models.person import Person
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Create a user and atomically create their self-person record.

    Steps:
    1. Insert user (person_id = NULL)
    2. Insert person (is_self = True, owner_id = user.id)
    3. Update user.person_id = person.id
    4. Commit once
    """
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        person_id=None,
    )
    db.add(user)
    await db.flush()  # assigns user.id without committing

    self_person = Person(
        id=uuid.uuid7(),
        owner_id=user.id,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        is_self=True,
    )
    db.add(self_person)
    await db.flush()  # assigns self_person.id

    user.person_id = self_person.id
    await db.commit()
    await db.refresh(user)
    return user
