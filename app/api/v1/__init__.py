from fastapi import APIRouter

from app.api.v1.assets import router as assets_router
from app.api.v1.auth import router as auth_router
from app.api.v1.interactions import router as interactions_router
from app.api.v1.iso_reference import router as iso_reference_router
from app.api.v1.notes import router as notes_router
from app.api.v1.persons import router as persons_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.vocabularies import router as vocabularies_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(persons_router)
api_router.include_router(assets_router)
api_router.include_router(interactions_router)
api_router.include_router(vocabularies_router)
api_router.include_router(iso_reference_router)
api_router.include_router(subscriptions_router)
api_router.include_router(notes_router)
api_router.include_router(tasks_router)
