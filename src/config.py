from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent


# Data directories
DATA_DIR = BASE_DIR / "data"

DOWNLOAD_DIR = DATA_DIR / "download"
UPLOAD_DIR = DATA_DIR / "upload"
OUTPUT_DIR = DATA_DIR / "output"


# Input file prefixes
BANK_A_FILE_PREFIX = "BANK_A_HISTORY"
BANK_B_FILE_PREFIX = "BANK_B_STATEMENT"


# Synthetic API configuration
# Replace with environment variables if a real API is ever connected.
API_ENDPOINT = "https://example.com/api/upload"
INGESTION_TOKEN = "synthetic-token"
INGESTION_PARENT_DIR = "payment_reconciliation"


# Synthetic Trino configuration
# Replace with environment variables if a real cluster is ever connected.
TRINO_HOST = "localhost"
TRINO_PORT = 8080
TRINO_USER = "synthetic-user"
TRINO_CATALOG = "synthetic_catalog"
TRINO_SCHEMA = "synthetic_schema"


# Synthetic Google Sheets configuration
GSHEET_SERVICE_ACCOUNT_FILE = "service_account.json"
GSHEET_SPREADSHEET_NAME = "Payment Reconciliation Outputs"