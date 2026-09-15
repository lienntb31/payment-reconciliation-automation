import re
import pandas as pd

from .utils import df_skip_header, reformat


def process_bank_a(files):
    """
    Prepare Bank A statement data for ingestion.

    Workflow:
    1. Read and concatenate statement files
    2. Remove headers and footer rows
    3. Select required columns
    4. Standardize column names
    5. Extract transaction trace/reference number
    6. Standardize data types
    7. Classify transactions
    """

    if not files:
        print("No Bank A files found.")
        return {}

    # --------------------------------------------------------
    # 1. Read and concatenate files
    # --------------------------------------------------------

    bank_a_data = pd.concat(
        [
            df_skip_header(
                file,
                keyword="Transaction Date",
            )
            for file in files
        ],
        ignore_index=True,
    )

    # --------------------------------------------------------
    # 2. Remove footer / invalid rows
    # --------------------------------------------------------

    bank_a_data.dropna(
        subset=["Value Date"],
        inplace=True,
    )

    # --------------------------------------------------------
    # 3. Standardize column names
    # --------------------------------------------------------

    bank_a_data.rename(
        columns={
            "Description": "Contents",
        },
        inplace=True,
    )

    # --------------------------------------------------------
    # 4. Keep required columns
    # --------------------------------------------------------

    bank_a = bank_a_data[
        [
            "Account No",
            "Transaction Date",
            "Value Date",
            "Contents",
            "Debit",
            "Credit",
            "Transaction Code",
        ]
    ].copy()

    # --------------------------------------------------------
    # 5. Extract English names from bilingual headers
    # --------------------------------------------------------

    bank_a.columns = [
        re.findall(
            r"\(([^)]+)\)",
            str(column),
        )[0]
        if "(" in str(column) and ")" in str(column)
        else column
        for column in bank_a.columns
    ]

    # --------------------------------------------------------
    # 6. Extract transaction trace/reference number
    # --------------------------------------------------------

    bank_a["Trace No"] = (
        bank_a["Contents"]
        .astype(str)
        .str.extract(
            r"(\d+)",
            expand=False,
        )
    )

    # --------------------------------------------------------
    # 7. Standardize data types
    # --------------------------------------------------------

    bank_a = reformat(
        bank_a,
        date_columns=["Value Date"],
        numeric_columns=[
            "Debit",
            "Credit",
        ],
    )

    # --------------------------------------------------------
    # 8. Classify transactions
    # --------------------------------------------------------

    detail = bank_a["Contents"].astype(str)

    # Disbursement
    bank_a_disbursement = bank_a[
        detail.str.contains(
            "DISBURSEMENT",
            case=False,
            na=False,
        )
    ].copy()

    # Repayment
    bank_a_repayment = bank_a[
        detail.str.contains(
            r"REPAYMENT|DEBT PAYMENT|REFUND",
            regex=True,
            case=False,
            na=False,
        )
    ].copy()

    # Other / unidentified transactions
    bank_a_other = bank_a[
        ~detail.str.contains(
            r"""
            DISBURSEMENT
            |REPAYMENT
            |DEBT PAYMENT
            |REFUND
            |INTERNAL.*TRANSFER
            |TAX
            |MANAGEMENT.*FEE
            |ADJUSTMENT
            """,
            regex=True,
            case=False,
            na=False,
        )
    ].copy()

    # --------------------------------------------------------
    # 9. Return processed datasets
    # --------------------------------------------------------

    return {
        "disbursement": bank_a_disbursement,
        "repayment": bank_a_repayment,
        "other": bank_a_other,
    }