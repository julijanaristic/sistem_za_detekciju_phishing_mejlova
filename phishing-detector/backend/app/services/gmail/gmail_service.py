import base64
import json
import os
from pathlib import Path 
from typing import Any

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from app.core.config import settings

from google.auth.transport.requests import Request 
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import Flow

class GmailService:
    def __init__(self) -> None:
        self.token_path: Path = settings.GMAIL_TOKEN_PATH
    
    @property
    def scopes(self) -> list[str]:
        return [settings.GOOGLE_GMAIL_SCOPE]
    
    def get_credentials(self) -> Credentials | None:
        if not self.token_path.exists():
            return None
        
        credentials = Credentials.from_authorized_user_file(
            self.token_path,
            self.scopes,
        )

        if credentials.valid:
            return credentials
        
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._save_credentials(credentials)
            return credentials
        
        return None
    
    def _save_credentials(
        self,
        credentials: Credentials,
        ) -> None:
        """Save OAuth credentials to the local token file."""

        self.token_path.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    def get_authorization_url(
        self,
        state: str,
        ) -> str:
        self._oauth_flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": (
                        "https://accounts.google.com/o/oauth2/auth"
                    ),
                    "token_uri": (
                        "https://oauth2.googleapis.com/token"
                    ),
                }
            },
            scopes=self.scopes,
            state=state,
        )

        self._oauth_flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

        authorization_url, _ = self._oauth_flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )

        return authorization_url
    
    def exchange_code_for_credentials(
        self,
        authorization_response: str,
        state: str,
    ) -> Credentials:
        if self._oauth_flow is None:
            raise RuntimeError(
                "OAuth flow is missing. Start with /gmail/connect."
            )

        self._oauth_flow.fetch_token(
            authorization_response=authorization_response
        )

        credentials = self._oauth_flow.credentials

        self._save_credentials(credentials)

        return credentials
    
    def is_connected(self) -> bool:
        return self.get_credentials() is not None

    def _get_gmail_service(self):
        credentials = self.get_credentials()

        if credentials is None:
            raise RuntimeError("Gmail account is not connected")

        return build(
            "gmail",
            "v1",
            credentials=credentials,
        )

    def list_messages(
        self,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        service = self._get_gmail_service()

        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=max_results,
            )
            .execute()
        )

        messages = response.get("messages", [])

        results: list[dict[str, Any]] = []

        for message in messages:
            message_id = message["id"]

            details = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=[
                        "Subject",
                        "From",
                        "Date",
                    ],
                )
                .execute()
            )

            headers = self._extract_headers(details)

            results.append(
                 {
                    "id": message_id,
                    "thread_id": message.get(
                        "threadId"
                    ),
                    "subject": headers.get(
                        "Subject",
                        "",
                    ),
                    "sender": headers.get(
                        "From",
                        "",
                    ),
                    "date": headers.get(
                        "Date",
                        "",
                    ),
                    "snippet": details.get(
                        "snippet",
                        "",
                    ),
                }
            )

        return results 
        
    def get_message(
        self, 
        message_id: str,
    ) -> dict[str, Any]:
        service = self._get_gmail_service()

        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

        headers = self._extract_headers(message)

        body = self._extract_body(message.get("payload", {}))

        return {
            "id": message_id,
            "thread_id": message.get(
                "threadId"
            ),
            "subject": headers.get(
                "Subject",
                "",
            ),
            "sender": headers.get(
                "From",
                "",
            ),
            "date": headers.get(
                "Date",
                "",
            ),
            "body": body,
            "snippet": message.get(
                "snippet",
                "",
            ),
        }
    
    @staticmethod
    def _extract_headers(
        message: dict[str, Any]
    ) -> dict[str, str]:
        headers = (
            message
            .get("payload", {})
            .get("headers", {})
        )

        result: dict[str, str] = {}

        for header in headers:
            name = header.get("name")
            value = header.get("value")

            if name and value:
                result[name] = value 
        
        return result 
    
    def _extract_body(
        self, 
        payload: dict[str, Any]
    ) -> str: 
        mime_type = payload.get("mimeType", "",)

        body_data = (
            payload
            .get("body", {})
            .get("data")
        )  

        if body_data and mime_type == "text/plain":
            return self._decode_body(body_data)
        
        parts = payload.get("parts", [])

        for part in parts:
            result = self._extract_body(part)

            if result.strip():
                return result
        
        if body_data:
            return self._decode_body(body_data)

        return ""

    @staticmethod
    def _decode_body(
        data: str,
    ) -> str:
        decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))

        return decoded.decode(
            "utf-8",
            errors="replace",
        )
    
    def disconnect(self) -> None:
        if self.token_path.exists():
            self.token_path.unlink()

gmail_service = GmailService()