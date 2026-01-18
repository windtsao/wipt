from wipt.config import load_config


def test_load_config_defaults(monkeypatch: object) -> None:
    monkeypatch.delenv("GMAIL_QUERY", raising=False)
    monkeypatch.delenv("GMAIL_MAX_RESULTS", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRETS_PATH", raising=False)
    monkeypatch.delenv("GOOGLE_TOKEN_PATH", raising=False)
    monkeypatch.delenv("SHEETS_SPREADSHEET_ID", raising=False)
    monkeypatch.delenv("SHEETS_WORKSHEET_NAME", raising=False)

    config = load_config()

    assert config.gmail_query == "has:attachment filename:pdf"
    assert config.gmail_max_results == 25
    assert config.google_client_secrets_path == ""
    assert config.google_token_path == ""
    assert config.sheets_spreadsheet_id == ""
    assert config.sheets_worksheet_name == "Sheet1"
