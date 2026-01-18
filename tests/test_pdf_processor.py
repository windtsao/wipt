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

    result = processor.extract_rows_from_text(sample_text)

    assert len(result.rows) == 1
    row = result.rows[0]
    assert row["client_info"] == "Serial Cables, LLC, 8811 American Way, Ste 110, Englewood, CO 80112"
    assert (
        row["ship_to_address"]
        == "Jwill Technology, #422-6, 46, Dolma-ro, Bundang-gu, Seongnam-si, Seonggi-do, 13630, Republic of Korea"
    )
    assert row["purchase_order_id"] == "PJM-10795"
    assert row["purchase_order_date"] == "1/5/2026"
    assert row["sales_person"] == "Justin Mutschler"
    assert row["due_date"] == "1/5/2026"
    assert row["item"] == "MCIO6-8X-39X2U2XC-1X4-0.5M"
    assert row["description"] == "Gen6 MCIO 8X (SFF-1016) 74P to *2"
    assert row["quantity"] == "10"
    assert row["price"] == "61.15"
    assert row["total"] == "611.50"


def test_pdf_processor_extracts_multiple_line_items() -> None:
    sample_text = "\n".join(
        [
            "Serial Cables, LLC",
            "8811 American Way",
            "Ste 110",
            "Englewood, CO 80112",
            "Purchase Order",
            "Date 12/5/2025",
            "P.O. No. PJM-10738",
            "Ship To",
            "Sanmina Corporation Plant 1337",
            "Attention: Janice McLemore",
            "540 E. Trimble Rd",
            "San Jose, CA 95131",
            "Salesperson",
            "Justin Mutschler",
            "Due Date",
            "3/8/2026",
            "CBL-01004-01-A UART AND PMBUS CABLE - NETFLIX GAMING ASROCKRACK STRIX HALO APU 6400 3.89 24896.00",
            "CBL-01016-01-A CABLE ASSY 24 PIN APU POWER WITH 4 PIN MINI-FIT JR ASROCK(6) 1165 11.67 13595.55",
        ]
    )

    processor = PdfProcessor()

    result = processor.extract_rows_from_text(sample_text)

    assert len(result.rows) == 2
    assert result.rows[0]["item"] == "CBL-01004-01-A"
    assert result.rows[0]["quantity"] == "6400"
    assert result.rows[0]["price"] == "3.89"
    assert result.rows[0]["total"] == "24896.00"
    assert result.rows[1]["item"] == "CBL-01016-01-A"
    assert result.rows[1]["quantity"] == "1165"
    assert result.rows[1]["price"] == "11.67"
    assert result.rows[1]["total"] == "13595.55"
