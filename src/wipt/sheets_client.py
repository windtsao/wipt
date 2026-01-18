from typing import Iterable


class SheetsClient:
    def __init__(self, spreadsheet_id: str, worksheet_name: str) -> None:
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name

    def append_row(self, row_values: Iterable[str]) -> None:
        """Append a row into the configured worksheet.

        TODO: Implement Google Sheets API integration.
        """
        _ = row_values
