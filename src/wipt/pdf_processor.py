from dataclasses import dataclass


@dataclass(frozen=True)
class PdfExtractionResult:
    fields: dict[str, str]


class PdfProcessor:
    def extract(self, pdf_bytes: bytes) -> PdfExtractionResult:
        """Extract structured fields from a PDF.

        TODO: Implement PDF parsing and field extraction.
        """
        placeholder_fields = {
            "field_one": "",
            "field_two": "",
            "field_three": "",
        }
        return PdfExtractionResult(fields=placeholder_fields)
