from abc import ABC, abstractmethod
from typing import Any 

class BasePhishingClassifier(ABC):
    @abstractmethod
    def predict(self, text: str) -> tuple[float, list[dict[str, Any]]]:
        pass
    
    @property
    @abstractmethod
    def is_ready(self) -> bool:
        pass
    
    @property
    @abstractmethod
    def model_version(self) -> str:
        pass
    
    @property
    @abstractmethod
    def active_model(self) -> str:
        pass