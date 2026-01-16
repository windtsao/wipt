from wipt.pdf_processor import PdfProcessor


def test_pdf_processor_returns_placeholder_fields() -> None:
    processor = PdfProcessor()

    result = processor.extract(b"%PDF-1.4 fake")

    assert result.fields == {
        "field_one": "",
        "field_two": "",
        "field_three": "",
    }
