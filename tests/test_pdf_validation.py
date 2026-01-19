from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from wipt.pdf_processor import PdfProcessor


def _normalize_text(value: str) -> str:
    cleaned = value.replace("\r", " ").replace("\n", " ").replace(",", " ")
    return " ".join(cleaned.split())


def _normalize_number(value: str) -> Decimal | None:
    if not value.strip():
        return None
    try:
        return Decimal(value.replace(",", ""))
    except InvalidOperation as exc:
        raise AssertionError(f"Expected a numeric value, got {value!r}") from exc


def test_pdf_matches_expected_csv_output() -> None:
    pdf_path = Path(__file__).with_name("PO_PJM10738_from_Serial_Cables_LLC_33924.pdf")
    csv_path = Path(__file__).with_name("Purchase Orders - test_data.csv")

    processor = PdfProcessor()
    result = processor.extract(pdf_path.read_bytes())

    with csv_path.open(newline="") as file:
        expected_rows = list(csv.DictReader(file))

    assert len(result.rows) == len(expected_rows)

    field_map = {
        "Process Time": "process_time",
        "Client Info": "client_info",
        "ShipTo Address": "ship_to_address",
        "Purchase Order Id": "purchase_order_id",
        "Purchase Order Date": "purchase_order_date",
        "Sales Person": "sales_person",
        "Due Date": "due_date",
        "Item": "item",
        "Description": "description",
        "Quantity": "quantity",
        "Price": "price",
        "Total": "total",
        "Status": "status",
        "Invoice Created?": "invoice_created",
        "PO Created?": "po_created",
    }

    for actual, expected in zip(result.rows, expected_rows):
        for csv_key, field_key in field_map.items():
            expected_value = expected[csv_key]
            actual_value = actual[field_key]
            if csv_key in {"Quantity", "Price", "Total"}:
                assert _normalize_number(actual_value) == _normalize_number(expected_value)
            else:
                assert _normalize_text(actual_value) == _normalize_text(expected_value)
