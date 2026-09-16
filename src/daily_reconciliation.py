from datetime import date, timedelta
from pathlib import Path

from src import config
from src.trino_client import get_connection, read_sql
from src.gsheet_client import get_client, write_dataframe


SQL_DIR = Path("sql")

RECON_OUTPUTS = {
    "Recon 1": {
        "1A_source_daily": "recon_01/01_source_daily.sql",
        "1B_transaction_daily": "recon_01/02_transaction_daily.sql",
        "1C_discrepancy_rca": "recon_01/03_discrepancy.sql",
    },

    "Recon 2": {
        "2A_transaction_daily": "recon_02/01_transaction_daily.sql",
        "2B_discrepancy_rca": "recon_02/02_discrepancy.sql",
    },

    "Recon 3": {
        "3A_funding_daily": "recon_03/01_settlement_daily.sql",
        "3B_discrepancy_rca": "recon_03/02_discrepancy.sql",
        "3C_bank_daily": "recon_03/03_bank_daily.sql",
        "3D_discrepancy_bank_rca": "recon_03/04_discrepancy_bank.sql",
    },

    "Recon 4": {
        "4A_payment_daily": "recon_04/01_payment_daily.sql",
        "4B_repayment_daily": "recon_04/02_repayment_daily.sql",
        "4C_discrepancy_rca": "recon_04/03_discrepancy.sql",
    },

    "Recon 5": {
        "5A_funding_daily": "recon_05/01_settlement_daily.sql",
        "5B_discrepancy_rca": "recon_05/02_discrepancy.sql",
        "5C_bank_daily": "recon_05/03_bank_daily.sql",
        "5D_discrepancy_bank_rca": "recon_05/04_discrepancy_bank.sql",
    },
}


def load_sql(filepath):
    return filepath.read_text(encoding="utf-8")


def render_sql(sql_template, start_date, end_date):
    """
    Fill in the `{{ start_date }}` / `{{ end_date }}` placeholders
    used by every reconciliation query in `sql/`.
    """

    return (
        sql_template
        .replace("{{ start_date }}", str(start_date))
        .replace("{{ end_date }}", str(end_date))
    )


def run_daily_reconciliation(
    trino_connection,
    gsheet_client,
    spreadsheet_name,
    start_date,
    end_date,
):

    for recon_name, outputs in RECON_OUTPUTS.items():

        for worksheet_name, sql_file in outputs.items():

            sql_path = SQL_DIR / sql_file

            sql = render_sql(
                load_sql(sql_path),
                start_date=start_date,
                end_date=end_date,
            )

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


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the daily reconciliation controls and publish results to Google Sheets."
    )
    parser.add_argument(
        "--start-date",
        help="Inclusive start date (YYYY-MM-DD). Defaults to yesterday.",
    )
    parser.add_argument(
        "--end-date",
        help="Exclusive end date (YYYY-MM-DD). Defaults to today.",
    )
    args = parser.parse_args()

    yesterday = date.today() - timedelta(days=1)
    start_date = args.start_date or yesterday.isoformat()
    end_date = args.end_date or date.today().isoformat()

    trino_connection = get_connection(
        host=config.TRINO_HOST,
        port=config.TRINO_PORT,
        user=config.TRINO_USER,
        catalog=config.TRINO_CATALOG,
        schema=config.TRINO_SCHEMA,
    )

    gsheet_client = get_client(config.GSHEET_SERVICE_ACCOUNT_FILE)

    run_daily_reconciliation(
        trino_connection=trino_connection,
        gsheet_client=gsheet_client,
        spreadsheet_name=config.GSHEET_SPREADSHEET_NAME,
        start_date=start_date,
        end_date=end_date,
    )


if __name__ == "__main__":
    main()