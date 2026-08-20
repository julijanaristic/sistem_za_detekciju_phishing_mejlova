from app.core.config import settings
from app.services.factory import ClassifierFactory

classifier = ClassifierFactory.create(
    model_name=settings.ACTIVE_MODEL
)