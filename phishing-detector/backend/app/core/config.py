from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "Phishing Email Detector API"
    API_V1_PREFIX: str = "/api/v1"

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    ACTIVE_MODEL: str = "baseline"

    PHISHING_THRESHOLD: float = 0.5

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    MODEL_DIR: Path = BASE_DIR / "ml" / "saved_models"

    VECTORIZER_PATH: Path = (
        MODEL_DIR / "tfidf_vectorizer.joblib"
    )

    MODEL_PATH: Path = (
        MODEL_DIR / "baseline_model.joblib"
    )

    BERT_MODEL_PATH: Path = (
        MODEL_DIR / "bert" / "final"
    )

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = ("http://localhost:8000/api/v1/gmail/oauth/callback")

    GOOGLE_GMAIL_SCOPE: str = ("https://www.googleapis.com/auth/gmail.readonly")

    GMAIL_TOKEN_PATH: Path = (BASE_DIR / ".gmail_token.json")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()