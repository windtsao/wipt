from dataclasses import dataclass
import io
import re



@dataclass(frozen=True)
class PdfExtractionResult:
    fields: dict[str, str]


class PdfProcessor:
    def extract(self, pdf_bytes: bytes) -> PdfExtractionResult:
        """Extract structured fields from a PDF.

        TODO: Refine PDF parsing rules once the exact layout rules are confirmed.
        """
        import pdfplumber

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        full_text = "\n".join(pages_text)
        return self.extract_from_text(full_text)

    def extract_from_text(self, text: str) -> PdfExtractionResult:
        line_item = _extract_line_item(text)
        fields = {
            "process_time": "",
            "client_info": ", ".join(_extract_header_block(text, "Purchase Order")),
            "ship_to_address": ", ".join(_extract_block(text, "Ship To", ("Salesperson", "Terms", "Due Date", "Item"))),
            "purchase_order_id": _extract_first_match(text, r"\bP\.O\.\s*No\.\s*([A-Za-z0-9-]+)"),
            "purchase_order_date": _extract_first_match(text, r"\bDate\s+(\d{1,2}/\d{1,2}/\d{4})"),
            "sales_person": _extract_first_match(text, r"\bSalesperson\s+([A-Za-z .'-]+)"),
            "due_date": _extract_first_match(text, r"\bDue Date\s+(\d{1,2}/\d{1,2}/\d{4})"),
            "item": line_item.item,
            "description": line_item.description,
            "quantity": line_item.quantity,
            "price": line_item.price,
            "total": line_item.total,
            "status": "",
            "invoice_created": "",
            "po_created": "",
        }
        return PdfExtractionResult(fields=fields)


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


def _extract_line_item(text: str) -> LineItem:
    lines = [line.strip() for line in text.splitlines()]
    line_item_pattern = re.compile(
        r"^(?P<item>[A-Za-z0-9.-]+)\s+(?P<description>.+?)\s+"
        r"(?P<quantity>\d+(?:\.\d+)?)\s+(?P<price>\d+(?:\.\d+)?)\s+"
        r"(?P<total>\d+(?:\.\d+)?)$"
    )
    for line in lines:
        match = line_item_pattern.search(line)
        if match:
            return LineItem(
                item=match.group("item"),
                description=match.group("description").strip(),
                quantity=match.group("quantity"),
                price=match.group("price"),
                total=match.group("total"),
            )
    return LineItem(item="", description="", quantity="", price="", total="")
