from dotenv import load_dotenv

from wipt.config import load_config
from wipt.gmail_client import GmailClient
from wipt.pdf_processor import PdfProcessor
from wipt.pdf_selector import PdfSelector
from wipt.sheets_client import SheetsClient


def main() -> None:
    load_dotenv()
    config = load_config()

    gmail_client = GmailClient(
        client_secrets_path=config.google_client_secrets_path,
        token_path=config.google_token_path,
    )
    pdf_selector = PdfSelector()
    pdf_processor = PdfProcessor()
    sheets_client = SheetsClient(
        spreadsheet_id=config.sheets_spreadsheet_id,
        worksheet_name=config.sheets_worksheet_name,
    )

    messages = gmail_client.fetch_messages(
        query=config.gmail_query,
        max_results=config.gmail_max_results,
    )

    for message in messages:
        selected_pdfs = pdf_selector.select(message.attachments)
        for pdf in selected_pdfs:
            extraction = pdf_processor.extract(pdf.data)
            for row in extraction.rows:
                row_values = [
                    row.get("process_time", ""),
                    row.get("client_info", ""),
                    row.get("ship_to_address", ""),
                    row.get("purchase_order_id", ""),
                    row.get("purchase_order_date", ""),
                    row.get("sales_person", ""),
                    row.get("due_date", ""),
                    row.get("item", ""),
                    row.get("description", ""),
                    row.get("quantity", ""),
                    row.get("price", ""),
                    row.get("total", ""),
                    row.get("status", ""),
                    row.get("invoice_created", ""),
                    row.get("po_created", ""),
                ]
                sheets_client.append_row(row_values)


if __name__ == "__main__":
    main()
