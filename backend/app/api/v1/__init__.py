from fastapi import APIRouter

from app.api.v1.addresses import router as addresses_router
from app.api.v1.asset_extensions import router as asset_extensions_router
from app.api.v1.assets import router as assets_router
from app.api.v1.auth import router as auth_router
from app.api.v1.budgets import router as budgets_router
from app.api.v1.channels import router as channels_router
from app.api.v1.communications import router as communications_router
from app.api.v1.documents import router as documents_router
from app.api.v1.events import event_persons_router, events_router
from app.api.v1.finances import router as finances_router
from app.api.v1.followups import router as followups_router
from app.api.v1.goals import router as goals_router
from app.api.v1.households import router as households_router
from app.api.v1.import_ import router as import_router
from app.api.v1.interactions import router as interactions_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.iso_reference import router as iso_reference_router
from app.api.v1.life_events import (
    life_events_router,
    life_events_standalone_router,
    significant_dates_router,
)
from app.api.v1.loans import person_loans_router
from app.api.v1.loans import router as loans_router
from app.api.v1.notes import router as notes_router
from app.api.v1.observations import router as observations_router
from app.api.v1.organizations import orgs_router, person_orgs_router
from app.api.v1.persons import router as persons_router
from app.api.v1.products import router as products_router
from app.api.v1.raven_logs import router as raven_logs_router
from app.api.v1.raven_questions import router as raven_questions_router
from app.api.v1.records import router as records_router
from app.api.v1.relationships import router as relationships_router
from app.api.v1.reminders import (
    asset_reminders_router,
    person_reminders_router,
    subscription_reminders_router,
)
from app.api.v1.reminders import (
    router as reminders_router,
)
from app.api.v1.renewals import router as renewals_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.vocabularies import router as vocabularies_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(households_router)
api_router.include_router(persons_router)
api_router.include_router(products_router)
api_router.include_router(inventory_router)
api_router.include_router(channels_router)
api_router.include_router(addresses_router)
api_router.include_router(relationships_router)
api_router.include_router(assets_router)
api_router.include_router(asset_extensions_router)
api_router.include_router(interactions_router)
api_router.include_router(life_events_standalone_router)
api_router.include_router(life_events_router)
api_router.include_router(significant_dates_router)
api_router.include_router(loans_router)
api_router.include_router(person_loans_router)
api_router.include_router(reminders_router)
api_router.include_router(person_reminders_router)
api_router.include_router(asset_reminders_router)
api_router.include_router(subscription_reminders_router)
api_router.include_router(observations_router)
api_router.include_router(followups_router)
api_router.include_router(goals_router)
api_router.include_router(orgs_router)
api_router.include_router(person_orgs_router)
api_router.include_router(events_router)
api_router.include_router(event_persons_router)
api_router.include_router(vocabularies_router)
api_router.include_router(iso_reference_router)
api_router.include_router(subscriptions_router)
api_router.include_router(transactions_router)
api_router.include_router(finances_router)
api_router.include_router(budgets_router)
api_router.include_router(notes_router)
api_router.include_router(tasks_router)
api_router.include_router(records_router)
api_router.include_router(documents_router)
api_router.include_router(renewals_router)
api_router.include_router(communications_router)
api_router.include_router(import_router)
api_router.include_router(raven_logs_router)
api_router.include_router(raven_questions_router)
