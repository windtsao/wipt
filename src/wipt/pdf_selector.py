from typing import Iterable, List

from wipt.gmail_client import GmailAttachment


class PdfSelector:
    def select(self, attachments: Iterable[GmailAttachment]) -> List[GmailAttachment]:
        """Return the PDF attachments that match selection rules.

        TODO: Implement selection rules (filename patterns, metadata, content).
        """
        return [attachment for attachment in attachments if attachment.filename.lower().endswith(".pdf")]
