from wipt.gmail_client import GmailAttachment
from wipt.pdf_selector import PdfSelector


def test_pdf_selector_filters_by_extension() -> None:
    attachments = [
        GmailAttachment(filename="statement.pdf", mime_type="application/pdf", data=b"pdf"),
        GmailAttachment(filename="notes.txt", mime_type="text/plain", data=b"text"),
        GmailAttachment(filename="SCAN.PDF", mime_type="application/pdf", data=b"scan"),
    ]

    selector = PdfSelector()

    selected = selector.select(attachments)

    assert [attachment.filename for attachment in selected] == ["statement.pdf", "SCAN.PDF"]
