from app.core.config import settings

from .base import BasePhishingClassifier
from .bert_classifier import BertPhishingClassifier
from .logistic_classifier import LogisticRegressionClassifier

class ClassifierFactory:
    @staticmethod
    def create(
        model_name: str,
    ) -> BasePhishingClassifier:
        model_name = model_name.lower().strip()

        if model_name == "baseline":
            return LogisticRegressionClassifier(
                model_path=settings.MODEL_PATH,
                vectorizer_path=settings.VECTORIZER_PATH
            )

        if model_name == "bert":
            return BertPhishingClassifier(
                model_path=settings.BERT_MODEL_PATH
            )
        
        raise ValueError(
            f"Unknown classifier: '{model_name}' "
            f"Supported models: baseline, bert"
        )