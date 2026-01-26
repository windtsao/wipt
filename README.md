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

### 3a) Gmail auth setup in Google Cloud (step-by-step)

1. Go to the Google Cloud Console and create or select a project:
   - https://console.cloud.google.com/
   - Use the project picker in the top bar to select an existing project or create a new one.
2. Enable the Gmail API:
   - Navigate to **APIs & Services → Library**.
   - Search for **Gmail API** and click **Enable**.
3. Configure the OAuth consent screen:
   - Go to **APIs & Services → OAuth consent screen**.
   - Choose **External** (personal Gmail) or **Internal** (Google Workspace).
   - Fill in the required app info (app name, user support email).
   - Under **Scopes**, you can leave defaults for now; Gmail scopes are added when the app runs.
   - If using **External**, add your Gmail address under **Test users**.
4. Create OAuth client credentials:
   - Go to **APIs & Services → Credentials**.
   - Click **Create Credentials → OAuth client ID**.
   - Choose **Desktop app** as the application type.
   - Create the client and download the JSON file.
   - Save it in your repo (example: `./secrets/gmail_client_secrets.json`).
5. Set environment variables in `.env`:
   - `GOOGLE_CLIENT_SECRETS_PATH=./secrets/gmail_client_secrets.json`
   - `GOOGLE_TOKEN_PATH=./secrets/gmail_token.json`
6. Run the app once to complete OAuth:
   - `python -m wipt.main`
   - A browser window will open; sign in to the Gmail account and approve access.
   - After approval, the token file will be written to `GOOGLE_TOKEN_PATH`.
7. Re-run the app normally; it will reuse the saved token until it expires.

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

## Deploying to Google Cloud

The easiest managed option is Cloud Run (serverless container). Below is a complete setup path
from enabling services to deploying and running the job.

### 1) Enable required Google Cloud services

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

> If you plan to run Gmail + Sheets on Cloud Run, ensure the Gmail API and Sheets API are
> enabled in the same project from **APIs & Services → Library**.

### 2) Create a service account and grant access

```bash
gcloud iam service-accounts create wipt-runner \
  --display-name "WIPT Cloud Run"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member "serviceAccount:wipt-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role "roles/secretmanager.secretAccessor"
```

If you plan to access Google Sheets via a service account, share the spreadsheet with
`wipt-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com`.

### 3) Store secrets in Secret Manager

Store your OAuth client secrets JSON and the generated token file as secrets:

```bash
gcloud secrets create gmail-client-secrets --data-file=./secrets/gmail_client_secrets.json
gcloud secrets create gmail-token --data-file=./secrets/gmail_token.json
```

### 4) Containerize the app

Create a `Dockerfile` that installs dependencies and runs the module:

```Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

COPY src ./src

CMD ["python", "-m", "wipt.main"]
```

### 5) Build and push the container

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/wipt
```

### 6) Deploy to Cloud Run

```bash
gcloud run deploy wipt \
  --image gcr.io/YOUR_PROJECT_ID/wipt \
  --region us-central1 \
  --platform managed \
  --service-account wipt-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-secrets GOOGLE_CLIENT_SECRETS_PATH=gmail-client-secrets:latest \
  --set-secrets GOOGLE_TOKEN_PATH=gmail-token:latest
```

### 7) Set runtime configuration

Set environment variables and mount or bake in secrets:

```bash
gcloud run services update wipt \
  --set-env-vars GMAIL_QUERY="has:attachment filename:pdf",GMAIL_MAX_RESULTS=25 \
  --set-env-vars SHEETS_SPREADSHEET_ID=YOUR_SHEET_ID,SHEETS_WORKSHEET_NAME=Sheet1
```

> Note: For Gmail OAuth on Cloud Run, pre-generate the refresh token locally (step 3a above)
> and store it securely in Secret Manager. The desktop OAuth flow (opening a browser window)
> is intended for local runs only.

## Next Steps

- Define Gmail filtering rules (labels, sender, subject, etc.).
- Define PDF selection rules (filename patterns, page count, content).
- Implement PDF parsing rules and map fields.
- Define spreadsheet column mapping.
