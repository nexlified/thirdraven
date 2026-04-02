from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.followup import FollowUpPublic
from app.schemas.goal import GoalPublic
from app.schemas.interaction import InteractionPublicRead
from app.schemas.life_event import LifeEventPublic, SignificantDatePublic
from app.schemas.observation import ObservationPublic
from app.schemas.organization import PersonOrgPublic
from app.schemas.person import PersonExtended, PersonSlim, RelationshipPublic


class RelationshipHealthEntry(BaseModel):
    person: PersonSlim
    last_contacted_on: date | None
    contact_frequency_days: int | None
    days_since_contact: int | None
    days_overdue: int | None  # negative = still within window
    health_status: str  # "on-track" | "due-soon" | "overdue" | "no-data"


class ContextPackage(BaseModel):
    person: PersonExtended
    relationships: list[RelationshipPublic]
    organizations: list[PersonOrgPublic]
    recent_interactions: list[InteractionPublicRead]
    upcoming_dates: list[SignificantDatePublic]
    life_events: list[LifeEventPublic]
    observations: list[ObservationPublic]
    pending_follow_ups: list[FollowUpPublic]
    goals: list[GoalPublic]
    generated_at: datetime
