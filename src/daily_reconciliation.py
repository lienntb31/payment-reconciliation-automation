from pathlib import Path

from src.trino_client import get_connection, read_sql
from src.gsheet_client import get_client, write_dataframe


SQL_DIR = Path("sql")

RECON_OUTPUTS = {
    "Recon 1": {
        "1A_upstream_daily": "recon_01/01_upstream_daily.sql",
        "1B_confirm_daily": "recon_01/02_confirm_daily.sql",
        "1C_discrepancy_rca": "recon_01/03_discrepancy.sql",
    },

    "Recon 2": {
        "2A_disburse_daily": "recon_02/01_disburse_daily.sql",
        "2B_discrepancy_rca": "recon_02/02_discrepancy.sql",
    },

    "Recon 3": {
        "3A_bank_daily": "recon_03/01_bank_daily.sql",
        "3B_discrepancy_rca": "recon_03/02_discrepancy.sql",
    },

    "Recon 4": {
        "4A_payment_daily": "recon_04/01_payment_daily.sql",
        "4B_repay_daily": "recon_04/02_repay_daily.sql",
        "4C_discrepancy_rca": "recon_04/03_discrepancy.sql",
    },

    "Recon 5": {
        "5A_bank_daily": "recon_05/01_bank_daily.sql",
        "5B_discrepancy_rca": "recon_05/02_discrepancy.sql",
    },
}


def load_sql(filepath):
    return filepath.read_text(encoding="utf-8")


def run_daily_reconciliation(
    trino_connection,
    gsheet_client,
    spreadsheet_name,
):

    for recon_name, outputs in RECON_OUTPUTS.items():

        for worksheet_name, sql_file in outputs.items():

            sql_path = SQL_DIR / sql_file

            sql = load_sql(sql_path)

            df = read_sql(
                sql,
                trino_connection,
            )

            write_dataframe(
                client=gsheet_client,
                spreadsheet_name=spreadsheet_name,
                worksheet_name=worksheet_name,
                df=df,
            )

            print(
                f"{recon_name} | "
                f"{worksheet_name} | "
                f"{len(df):,} rows"
            )