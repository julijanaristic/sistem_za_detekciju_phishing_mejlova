from pathlib import Path 
from typing import Any

import joblib
import numpy as np 

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from .base import BasePhishingClassifier

class LogisticRegressionClassifier(BasePhishingClassifier):
    def __init__(
        self,
        model_path: Path,
        vectorizer_path: Path,
    ):
        self.model_path = model_path 
        self.vectorizer_path = vectorizer_path

        self.model: LogisticRegression | None = None
        self.vectorizer: TfidfVectorizer | None = None

        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Logistic Regression model not found: "
                f"{self.model_path}"
            )
        
        if not self.vectorizer_path.exists():
            raise FileNotFoundError(
                f"TF-IDF vectorizer not found: "
                f"{self.vectorizer_path}"
            )
        
        self.model = joblib.load(self.model_path)
        self.vectorizer = joblib.load(self.vectorizer_path)
    
    @property
    def is_ready(self) -> bool:
        return (
            self.model is not None and self.vectorizer is not None
        )
    
    @property
    def model_version(self) -> str:
        return "baseline-tfidf-logreg-v1"

    @property
    def active_model(self) -> str:
        return "baseline"

    def predict(
        self,
        text: str,
    ) -> tuple[float, list[dict[str, Any]]]:
        if not self.is_ready:
            raise RuntimeError(
                "Logistic regression classifier is not ready"
            )
        
        if not text or not text.strip():
            raise ValueError("Email text cannot be empty")
        
        assert self.model is not None
        assert self.vectorizer is not None 

        X = self.vectorizer.transform([text])

        phishing_probability = float(
            self.model.predict_proba(X)[0][1]
        )

        suspicious_tokens = self._get_suspicious_tokens(X)
        return phishing_probability, suspicious_tokens
    
    def _get_suspicious_tokens(
        self,
        X,
        top_n: int = 10,
    ) -> list[dict[str, Any]]:
        assert self.model is not None 
        assert self.vectorizer is not None 

        feature_names = np.array(
            self.vectorizer.get_feature_names_out()
        )

        tfidf_values = X.toarray()[0]

        coefficients = self.model.coef_[0]

        contributions = tfidf_values * coefficients

        phishing_indices = np.where(contributions > 0)[0]

        if len(phishing_indices) == 0:
            return []

        sorted_indices = phishing_indices[
            np.argsort(
                contributions[phishing_indices]
            )[::-1]
        ]

        results = []

        for index in sorted_indices[:top_n]:
            results.append(
                {
                    "token": str(feature_names[index]),
                    "weight": round(
                        float(contributions[index]),
                        4,
                    ),
                }
            )
        
        return results