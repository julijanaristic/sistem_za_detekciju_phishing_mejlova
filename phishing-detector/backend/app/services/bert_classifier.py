from pathlib import Path
from typing import Any 

import torch 
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from .base import BasePhishingClassifier

class BertPhishingClassifier(BasePhishingClassifier):
    def __init__(
        self,
        model_path: Path,
        max_length: int = 256,
    ):
        self.model_path = model_path
        self.max_length = max_length

        self.tokenizer = None
        self.model = None 

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self._load_model()
    
    def _load_model(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"BERT model directory not found: "
                f"{self.model_path}"
            )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path
        )

        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_path
        )

        self.model.to(self.device)
        self.model.eval()

    @property
    def is_ready(self) -> bool:
        return (
            self.model is not None
            and self.tokenizer is not None
        )

    @property
    def model_version(self) -> str:
        return "bert-distilbert-v1"
    
    @property
    def active_model(self) -> str:
        return "bert"
    
    def predict(
        self,
        text: str,
    ) -> tuple[float, list[dict[str, Any]]]:
        if not self.is_ready:
            raise RuntimeError(
                "BERT classifier is not ready"
            )
        
        if not text or not text.strip():
            raise ValueError("Email text cannot be empty")
        
        assert self.model is not None
        assert self.tokenizer is not None 

        inputs = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=self.max_length,
            return_tensors="pt"
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
            if key != "token_type_ids"
        }

        with torch.no_grad():
            outputs = self.model(**inputs)

        probabilities = torch.softmax(
            outputs.logits,
            dim=1,
        )

        phishing_probability = float(
            probabilities[0][1].item()
        )

        suspicious_tokens: list[dict[str, Any]] = []

        return phishing_probability, suspicious_tokens