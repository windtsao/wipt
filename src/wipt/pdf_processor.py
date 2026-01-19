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
            pages = list(pdf.pages)
            pages_text = [page.extract_text() or "" for page in pages]
        full_text = "\n".join(pages_text)
        base_fields = _extract_base_fields_from_pages(pages, full_text)
        return _build_result_rows(full_text, base_fields)

    def extract_rows_from_text(self, text: str) -> PdfExtractionResult:
        base_fields = _extract_base_fields_from_text(text)
        return _build_result_rows(text, base_fields)


def _build_result_rows(text: str, base_fields: dict[str, str]) -> PdfExtractionResult:
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


def _extract_base_fields_from_text(text: str) -> dict[str, str]:
    purchase_order_date = _extract_first_match(text, r"\bDate\s+(\d{1,2}/\d{1,2}/\d{4})")
    return {
        "process_time": purchase_order_date,
        "client_info": ", ".join(_extract_header_block(text, "Purchase Order")),
        "ship_to_address": ", ".join(_extract_block(text, "Ship To", ("Salesperson", "Terms", "Due Date", "Item"))),
        "purchase_order_id": _extract_first_match(text, r"\bP\.O\.\s*No\.\s*([A-Za-z0-9-]+)"),
        "purchase_order_date": purchase_order_date,
        "sales_person": _extract_first_match(text, r"\bSalesperson\s+([A-Za-z .'-]+)"),
        "due_date": _extract_first_match(text, r"\bDue Date\s+(\d{1,2}/\d{1,2}/\d{4})"),
        "status": "NEW",
        "invoice_created": "No",
        "po_created": "No",
    }


def _extract_base_fields_from_pages(pages: list[object], text: str) -> dict[str, str]:
    for page in pages:
        try:
            columns = _extract_column_lines(page)
        except Exception:
            columns = []
        if columns:
            base_fields = _extract_base_fields_from_columns(columns)
            if base_fields["purchase_order_id"] or base_fields["purchase_order_date"]:
                return base_fields
    return _extract_base_fields_from_text(text)


def _extract_column_lines(page: object) -> list[tuple[str, str]]:
    words = page.extract_words() if hasattr(page, "extract_words") else []
    if not words:
        return []
    words.sort(key=lambda word: (word["top"], word["x0"]))
    threshold = getattr(page, "width", 0) * 0.45
    if threshold == 0:
        threshold = 275
    lines: list[list[dict[str, float | str]]] = []
    current_top: float | None = None
    for word in words:
        top = float(word["top"])
        if current_top is None or abs(top - current_top) > 2:
            lines.append([word])
            current_top = top
        else:
            lines[-1].append(word)
    columns: list[tuple[str, str]] = []
    for line_words in lines:
        left_words = [w for w in line_words if float(w["x0"]) < threshold]
        right_words = [w for w in line_words if float(w["x0"]) >= threshold]
        left = " ".join(w["text"] for w in left_words).strip()
        right = " ".join(w["text"] for w in right_words).strip()
        columns.append((left, right))
    return columns


def _extract_base_fields_from_columns(columns: list[tuple[str, str]]) -> dict[str, str]:
    vendor_index = None
    for index, (left, right) in enumerate(columns):
        if "Vendor" in left and "Ship" in right:
            vendor_index = index
            break
    client_info_lines: list[str] = []
    if vendor_index is not None:
        for left, _ in columns[:vendor_index]:
            if left:
                client_info_lines.append(left)
    ship_to_lines: list[str] = []
    if vendor_index is not None:
        for _, right in columns[vendor_index + 1 :]:
            if "Salesperson" in right:
                break
            if right:
                ship_to_lines.append(right)

    purchase_order_date = ""
    purchase_order_id = ""
    date_pattern = re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b")
    po_pattern = re.compile(r"\b[A-Za-z]{2,5}-\d+\b")
    for _, right in columns:
        if not purchase_order_date:
            match = date_pattern.search(right)
            if match:
                purchase_order_date = match.group(0)
        if not purchase_order_id:
            match = po_pattern.search(right)
            if match:
                purchase_order_id = match.group(0)
        if purchase_order_date and purchase_order_id:
            break

    sales_person = ""
    due_date = ""
    for index, (_, right) in enumerate(columns):
        if "Salesperson" in right:
            if index + 1 < len(columns):
                value_line = columns[index + 1][1]
                due_date_match = re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", value_line)
                if due_date_match:
                    due_date = due_date_match.group(0)
                else:
                    due_date = ""
                sales_person = value_line.replace(due_date, "").strip()
            break

    return {
        "process_time": purchase_order_date,
        "client_info": ", ".join(client_info_lines),
        "ship_to_address": ", ".join(ship_to_lines),
        "purchase_order_id": purchase_order_id,
        "purchase_order_date": purchase_order_date,
        "sales_person": sales_person,
        "due_date": due_date,
        "status": "NEW",
        "invoice_created": "No",
        "po_created": "No",
    }

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
        if line.startswith("PO#") or line.startswith("Deliver by") or line == "Total" or line.startswith("$"):
            flush_current()
            break
        direct_match = line_item_pattern.search(line)
        if direct_match:
            flush_current()
            current_item = LineItem(
                item=direct_match.group("item"),
                description="",
                quantity=direct_match.group("quantity"),
                price=direct_match.group("price"),
                total=direct_match.group("total"),
            )
            description = direct_match.group("description").strip()
            if description:
                description_parts.append(description)
            continue

        parts = line.split()
        if parts and item_code_pattern.match(parts[0]):
            remainder = line[len(parts[0]) :].strip()
            trailing_match = trailing_numbers_pattern.search(remainder) if remainder else None
            if trailing_match:
                flush_current()
                current_item = LineItem(item=parts[0], description="", quantity="", price="", total="")
                description = remainder[: trailing_match.start()].strip()
                current_item = LineItem(
                    item=current_item.item,
                    description="",
                    quantity=trailing_match.group("quantity"),
                    price=trailing_match.group("price"),
                    total=trailing_match.group("total"),
                )
                if description:
                    description_parts.append(description)
            else:
                if current_item:
                    description_parts.append(line)
                else:
                    flush_current()
                    current_item = LineItem(item=parts[0], description="", quantity="", price="", total="")
                    if remainder:
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
