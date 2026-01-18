from dataclasses import dataclass
import io
import re



@dataclass(frozen=True)
class PdfExtractionResult:
    rows: list[dict[str, str]]


class PdfProcessor:
    def extract(self, pdf_bytes: bytes) -> PdfExtractionResult:
        """Extract structured fields from a PDF.

        TODO: Refine PDF parsing rules once the exact layout rules are confirmed.
        """
        import pdfplumber

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        full_text = "\n".join(pages_text)
        return self.extract_rows_from_text(full_text)

    def extract_rows_from_text(self, text: str) -> PdfExtractionResult:
        base_fields = {
            "process_time": "",
            "client_info": ", ".join(_extract_header_block(text, "Purchase Order")),
            "ship_to_address": ", ".join(_extract_block(text, "Ship To", ("Salesperson", "Terms", "Due Date", "Item"))),
            "purchase_order_id": _extract_first_match(text, r"\bP\.O\.\s*No\.\s*([A-Za-z0-9-]+)"),
            "purchase_order_date": _extract_first_match(text, r"\bDate\s+(\d{1,2}/\d{1,2}/\d{4})"),
            "sales_person": _extract_first_match(text, r"\bSalesperson\s+([A-Za-z .'-]+)"),
            "due_date": _extract_first_match(text, r"\bDue Date\s+(\d{1,2}/\d{1,2}/\d{4})"),
            "status": "",
            "invoice_created": "",
            "po_created": "",
        }
        line_items = _extract_line_items(text)
        rows: list[dict[str, str]] = []
        if not line_items:
            rows.append(
                {
                    **base_fields,
                    "item": "",
                    "description": "",
                    "quantity": "",
                    "price": "",
                    "total": "",
                }
            )
        else:
            for line_item in line_items:
                rows.append(
                    {
                        **base_fields,
                        "item": line_item.item,
                        "description": line_item.description,
                        "quantity": line_item.quantity,
                        "price": line_item.price,
                        "total": line_item.total,
                    }
                )
        return PdfExtractionResult(rows=rows)


def _extract_first_match(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    if not match:
        return ""
    return match.group(1).strip()


def _extract_block(text: str, header: str, stop_headers: tuple[str, ...]) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    start_index = None
    for index, line in enumerate(lines):
        if line == header:
            start_index = index + 1
            break
    if start_index is None:
        return []

    block_lines: list[str] = []
    for line in lines[start_index:]:
        if not line:
            continue
        if line in stop_headers:
            break
        block_lines.append(line)
    return block_lines


def _extract_header_block(text: str, stop_header: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    header_lines: list[str] = []
    for line in lines:
        if line == stop_header:
            break
        if line:
            header_lines.append(line)
    return header_lines


@dataclass(frozen=True)
class LineItem:
    item: str
    description: str
    quantity: str
    price: str
    total: str


def _extract_line_items(text: str) -> list[LineItem]:
    lines = [line.strip() for line in text.splitlines()]
    item_code_pattern = re.compile(r"^(?=.*\d)(?=.*-)[A-Za-z0-9-]+$")
    line_item_pattern = re.compile(
        r"^(?P<item>[A-Za-z0-9.-]+)\s+(?P<description>.+?)\s+"
        r"(?P<quantity>\d[\d,]*)\s+(?P<price>\d[\d,]*\.\d{2})\s+"
        r"(?P<total>\d[\d,]*\.\d{2})$"
    )
    trailing_numbers_pattern = re.compile(
        r"(?P<quantity>\d[\d,]*)\s+(?P<price>\d[\d,]*\.\d{2})\s+(?P<total>\d[\d,]*\.\d{2})$"
    )
    items: list[LineItem] = []
    current_item: LineItem | None = None
    description_parts: list[str] = []

    def flush_current() -> None:
        nonlocal current_item, description_parts
        if current_item:
            description = " ".join(description_parts).strip()
            items.append(
                LineItem(
                    item=current_item.item,
                    description=description,
                    quantity=current_item.quantity,
                    price=current_item.price,
                    total=current_item.total,
                )
            )
        current_item = None
        description_parts = []

    for line in lines:
        if not line:
            continue
        direct_match = line_item_pattern.search(line)
        if direct_match:
            flush_current()
            items.append(
                LineItem(
                    item=direct_match.group("item"),
                    description=direct_match.group("description").strip(),
                    quantity=direct_match.group("quantity"),
                    price=direct_match.group("price"),
                    total=direct_match.group("total"),
                )
            )
            continue

        parts = line.split()
        if parts and item_code_pattern.match(parts[0]):
            flush_current()
            current_item = LineItem(item=parts[0], description="", quantity="", price="", total="")
            remainder = line[len(parts[0]) :].strip()
            if remainder:
                trailing_match = trailing_numbers_pattern.search(remainder)
                if trailing_match:
                    description = remainder[: trailing_match.start()].strip()
                    current_item = LineItem(
                        item=current_item.item,
                        description="",
                        quantity=trailing_match.group("quantity"),
                        price=trailing_match.group("price"),
                        total=trailing_match.group("total"),
                    )
                    description_parts.append(description)
                else:
                    description_parts.append(remainder)
            continue

        if current_item:
            trailing_match = trailing_numbers_pattern.search(line)
            if trailing_match and not current_item.quantity:
                description = line[: trailing_match.start()].strip()
                description_parts.append(description)
                current_item = LineItem(
                    item=current_item.item,
                    description="",
                    quantity=trailing_match.group("quantity"),
                    price=trailing_match.group("price"),
                    total=trailing_match.group("total"),
                )
            else:
                description_parts.append(line)

    flush_current()
    return items
