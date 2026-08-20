from pydantic import BaseModel, Field

class EmailClassifyRequest(BaseModel):
    subject: str = Field(default="", description="Email subject")
    body: str = Field(..., description="Email body (plain text or HTML)")
    sender: str | None = Field(default=None, description="From address, if known")

class SuspiciousToken(BaseModel):
    token: str
    weight: float

class UrlFinding(BaseModel):
    url: str
    is_suspicious: bool
    reason: str | None = None

class EmailClassifyResponse(BaseModel):
    label: str # "phishing" or "legitimate"
    phishing_probability: float # 0.0 - 1.0
    suspicious_tokens: list[SuspiciousToken] = []
    url_findings: list[UrlFinding] = []
    model_version: str = "baseline-tfidf-logreg-v1"