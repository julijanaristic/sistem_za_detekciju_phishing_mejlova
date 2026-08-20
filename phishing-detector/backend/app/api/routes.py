import secrets

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.models.schemas import EmailClassifyRequest, EmailClassifyResponse
from app.services.classifier import classifier
from app.services import feature_extraction as fx
from app.services.gmail.gmail_service import gmail_service

router = APIRouter()
oauth_states: set[str] = set()

@router.get("/health")
def health_check():
    return {
        "status": "ok", 
        "model_ready": classifier.is_ready,
        "active_model": classifier.active_model,
        "model_version": classifier.model_version
    } 

@router.post("/classify", response_model=EmailClassifyResponse)
def classify_email(payload: EmailClassifyRequest):
    if not classifier.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Classifier is not ready.",
        )

    full_text = (f"{payload.subject}\n{payload.body}")
    try:
        phishing_proba, suspicious_tokens = (
            classifier.predict(full_text)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if fx.is_legitimate_sender(payload.sender):
        phishing_proba *= 0.4

    url_findings = fx.analyze_urls_in_text(
        payload.body
    )

    label = (
        "phishing"
        if phishing_proba >= settings.PHISHING_THRESHOLD
        else "legitimate"
    )
    
    return EmailClassifyResponse(
        label=label,
        phishing_probability=round(
            phishing_proba,
            4,
        ),
        suspicious_tokens=suspicious_tokens,
        url_findings=url_findings,
        model_version=classifier.model_version
    )

@router.get("/gmail/connect")
def connect_gmail():
    state = secrets.token_urlsafe(32)

    oauth_states.add(state)

    authorization_url = (
        gmail_service.get_authorization_url(state=state)
    )

    return RedirectResponse(url=authorization_url)

@router.get("/gmail/oauth/callback")
def gmail_oauth_callback(
    request: Request,
): 
    returned_state = request.query_params.get("state")

    if not returned_state:
        raise HTTPException(
            status_code=400,
            detail="OAuth state is missing.",
        )

    if returned_state not in oauth_states:
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state.",
        )
    
    code = request.query_params.get(
        "code"
    )

    if not code:
        error = request.query_params.get(
            "error"
        )

        raise HTTPException(
            status_code=400,
            detail=(
                f"Google authorization failed: "
                f"{error or 'unknown error'}"
            ),
        )

    try:
        gmail_service.exchange_code_for_credentials(
            authorization_response=str(request.url),
            state=returned_state,
        )
    
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect Gmail: {exc}",
        )
    
    oauth_states.discard(returned_state)

    return RedirectResponse(
        url="http://localhost:5173/?gmail=connected"
    )

@router.get("/gmail/status")
def gmail_status():
    return {
        "connected": gmail_service.is_connected()
    }

@router.get("/gmail/messages")
def list_gmail_message(
    limit: int = 10,
):
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 50.",
        )

    if not gmail_service.is_connected():
        raise HTTPException(
            status_code=401,
            detail="Gmail account is not connected.",
        )
    
    try:
        messages = gmail_service.list_messages(
            max_results=limit 
        )

        return {
            "messages": messages
        }
    
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Gmail messages: {exc}"
        )

@router.get("/gmail/messages/{message_id}")
def get_gmail_message(
    message_id: str,
):
    if not gmail_service.is_connected():
        raise HTTPException(
            status_code=401,
            detail="Gmail account is not connected.",
        )
    
    try:
        message = gmail_service.get_message(message_id)

        return message 
    
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Gmail message: {exc}",
        )

@router.post(
    "/gmail/messages/{message_id}/analyze",
    response_model=EmailClassifyResponse,
)
def analyze_gmail_message(
    message_id: str,
):
    if not classifier.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Classifier is not ready.",
        )

    if not gmail_service.is_connected():
        raise HTTPException(
            status_code=401,
            detail="Gmail account is not connected.",
        )
    
    try:
        message = gmail_service.get_message(message_id)

        full_text = (
            f"{message['subject']}\n"
            f"{message['body']}"
        )
        
        phishing_proba, suspicious_tokens = (
            classifier.predict(full_text)
        )

        if fx.is_legitimate_sender(message["sender"]):
            phishing_proba *= 0.4

        url_findings = (
            fx.analyze_urls_in_text(message["body"])
        )

        label = (
            "phishing"
            if phishing_proba >= settings.PHISHING_THRESHOLD
            else "legitimate"
        )

        return EmailClassifyResponse(
            label=label,
            phishing_probability=round(
                phishing_proba,
                4,
            ),
            suspicious_tokens=suspicious_tokens,
            url_findings=url_findings,
            model_version=classifier.model_version,
        )
    
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to analyze Gmail message: "
                f"{exc}"
            ),
        )
    
@router.post("/gmail/disconnect")
def disconnect_gmail():
    gmail_service.disconnect()

    return {
        "status": "disconnected",
        "message": "Gmail account disconnected successfully",
    }
    
