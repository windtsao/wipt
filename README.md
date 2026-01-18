# WIPT: Gmail PDF Intake to Spreadsheet

This project is a starting scaffold for ingesting specific emails from a Gmail inbox, selecting the correct PDF attachment, extracting information from that PDF, and appending rows into a spreadsheet. The extraction and selection rules are intentionally left as placeholders for future expansion.

## Overview

The current flow is:

1. Fetch candidate emails from a Gmail inbox.
2. Select relevant PDF attachments based on rules (to be defined).
3. Process the PDF into structured fields (placeholders).
4. Append a new row to a spreadsheet (Google Sheets).

## Getting Started

### 1) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 3) Configure environment

Copy `.env.example` to `.env` and fill in the values. Google credentials can be generated via a Google Cloud project with Gmail and Sheets APIs enabled.

### 4) Run

```bash
python -m wipt.main
```

### 4a) Integration-style extraction check (local PDF)

```bash
python -m wipt.cli extract --pdf /path/to/file.pdf
```

This prints extracted rows as JSON (one per line item). Right now they are placeholders until the PDF rules are defined.

Extracted fields currently include: `process_time`, `client_info`, `ship_to_address`, `purchase_order_id`, `purchase_order_date`, `sales_person`, `due_date`, `item`, `description`, `quantity`, `price`, `total`, `status`, `invoice_created`, `po_created`.

### 5) Run tests

```bash
pytest
```

## Next Steps

- Define Gmail filtering rules (labels, sender, subject, etc.).
- Define PDF selection rules (filename patterns, page count, content).
- Implement PDF parsing rules and map fields.
- Define spreadsheet column mapping.
