from wipt.pdf_processor import PdfProcessor


def test_pdf_processor_extracts_purchase_order_fields() -> None:
    sample_text = "\n".join(
        [
            "Serial Cables, LLC",
            "8811 American Way",
            "Ste 110",
            "Englewood, CO 80112",
            "Purchase Order",
            "Date 1/5/2026",
            "P.O. No. PJM-10795",
            "Ship To",
            "Jwill Technology",
            "#422-6, 46, Dolma-ro, Bundang-gu",
            "Seongnam-si, Seonggi-do, 13630",
            "Republic of Korea",
            "Salesperson",
            "Justin Mutschler",
            "Due Date",
            "1/5/2026",
            "MCIO6-8X-39X2U2XC-1X4-0.5M Gen6 MCIO 8X (SFF-1016) 74P to *2 10 61.15 611.50",
        ]
    )
    processor = PdfProcessor()

    result = processor.extract_from_text(sample_text)

    assert result.fields["client_info"] == "Serial Cables, LLC, 8811 American Way, Ste 110, Englewood, CO 80112"
    assert (
        result.fields["ship_to_address"]
        == "Jwill Technology, #422-6, 46, Dolma-ro, Bundang-gu, Seongnam-si, Seonggi-do, 13630, Republic of Korea"
    )
    assert result.fields["purchase_order_id"] == "PJM-10795"
    assert result.fields["purchase_order_date"] == "1/5/2026"
    assert result.fields["sales_person"] == "Justin Mutschler"
    assert result.fields["due_date"] == "1/5/2026"
    assert result.fields["item"] == "MCIO6-8X-39X2U2XC-1X4-0.5M"
    assert result.fields["description"] == "Gen6 MCIO 8X (SFF-1016) 74P to *2"
    assert result.fields["quantity"] == "10"
    assert result.fields["price"] == "61.15"
    assert result.fields["total"] == "611.50"
