from dataclasses import dataclass
from typing import Iterable, List


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

    def fetch_messages(self, query: str, max_results: int) -> Iterable[GmailMessage]:
        """Fetch candidate messages from Gmail.

        TODO: Implement Gmail API integration and return messages with attachments.
        """
        return []
