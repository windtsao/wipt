from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    gmail_query: str
    gmail_max_results: int
    google_client_secrets_path: str
    google_token_path: str
    sheets_spreadsheet_id: str
    sheets_worksheet_name: str


def load_config() -> AppConfig:
    gmail_query = os.getenv("GMAIL_QUERY", "has:attachment filename:pdf")
    gmail_max_results = int(os.getenv("GMAIL_MAX_RESULTS", "25"))
    return AppConfig(
        gmail_query=gmail_query,
        gmail_max_results=gmail_max_results,
        google_client_secrets_path=os.getenv("GOOGLE_CLIENT_SECRETS_PATH", ""),
        google_token_path=os.getenv("GOOGLE_TOKEN_PATH", ""),
        sheets_spreadsheet_id=os.getenv("SHEETS_SPREADSHEET_ID", ""),
        sheets_worksheet_name=os.getenv("SHEETS_WORKSHEET_NAME", "Sheet1"),
    )
