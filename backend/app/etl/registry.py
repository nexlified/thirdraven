from app.etl.base import BaseImportHandler
from app.etl.handlers.contact import ContactImportHandler

HANDLER_REGISTRY: dict[str, type[BaseImportHandler]] = {
    "contact": ContactImportHandler,
}
