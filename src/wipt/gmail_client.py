from __future__ import annotations

from dataclasses import dataclass
import base64
import os
from typing import Dict, Iterable, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


@dataclass(frozen=True)
class GmailAttachment:
    filename: str
    mime_type: str
    data: bytes


@dataclass(frozen=True)
class GmailMessage:
    message_id: str
    subject: str
    attachments: List[GmailAttachment]


class GmailClient:
    def __init__(self, client_secrets_path: str, token_path: str) -> None:
        self.client_secrets_path = client_secrets_path
        self.token_path = token_path
        self._scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

    def fetch_messages(self, query: str, max_results: int) -> Iterable[GmailMessage]:
        """Fetch candidate messages from Gmail.

        Returns messages containing attachment payloads based on the query.
        """
        service = self._build_service()
        response = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = response.get("messages", [])
        results: List[GmailMessage] = []
        for message in messages:
            message_id = message["id"]
            full_message = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            payload = full_message.get("payload", {})
            subject = self._extract_subject(payload.get("headers", []))
            attachments = self._extract_attachments(service, message_id, payload)
            results.append(
                GmailMessage(
                    message_id=message_id,
                    subject=subject,
                    attachments=attachments,
                )
            )
        return results

    def _build_service(self):
        creds = self._load_credentials()
        return build("gmail", "v1", credentials=creds)

    def _load_credentials(self) -> Credentials:
        creds: Optional[Credentials] = None
        if self.token_path and os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self._scopes)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_path,
                self._scopes,
            )
            creds = flow.run_local_server(port=0)
            if self.token_path:
                with open(self.token_path, "w", encoding="utf-8") as token_file:
                    token_file.write(creds.to_json())
        return creds

    @staticmethod
    def _extract_subject(headers: Iterable[Dict[str, str]]) -> str:
        for header in headers:
            if header.get("name", "").lower() == "subject":
                return header.get("value", "")
        return ""

    def _extract_attachments(
        self,
        service,
        message_id: str,
        payload: Dict[str, object],
    ) -> List[GmailAttachment]:
        attachments: List[GmailAttachment] = []
        stack = [payload]
        while stack:
            part = stack.pop()
            if not part:
                continue
            filename = part.get("filename")
            body = part.get("body", {})
            mime_type = part.get("mimeType", "")
            if filename:
                data = self._get_attachment_data(service, message_id, body)
                if data:
                    attachments.append(
                        GmailAttachment(
                            filename=filename,
                            mime_type=mime_type,
                            data=data,
                        )
                    )
            for subpart in part.get("parts", []) or []:
                stack.append(subpart)
        return attachments

    def _get_attachment_data(
        self,
        service,
        message_id: str,
        body: Dict[str, object],
    ) -> bytes:
        data = body.get("data")
        if data:
            return base64.urlsafe_b64decode(data.encode("utf-8"))
        attachment_id = body.get("attachmentId")
        if not attachment_id:
            return b""
        attachment = (
            service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        attachment_data = attachment.get("data")
        if not attachment_data:
            return b""
        return base64.urlsafe_b64decode(attachment_data.encode("utf-8"))
