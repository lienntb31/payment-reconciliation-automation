import numpy as np
import pandas as pd

from .utils import df_skip_header, reformat


def process_bank_b(files):
    """
    Prepare Bank B statement data for ingestion.

    Workflow:
    1. Read and concatenate statement files
    2. Remove headers and footer rows
    3. Select required columns
    4. Extract transaction trace/reference number
    5. Standardize data types
    6. Classify transactions
    """

    if not files:
        print("No Bank B files found.")
        return {}

    # --------------------------------------------------------
    # 1. Read and concatenate files
    # --------------------------------------------------------

    bank_b_data = pd.concat(
        [
            df_skip_header(
                file,
                keyword="Transaction ID",
                col_idx=1,
            )
            for file in files
        ],
        ignore_index=True,
    )

    # --------------------------------------------------------
    # 2. Remove footer / invalid rows
    # --------------------------------------------------------

    bank_b_data.dropna(
        subset=["Value Date"],
        inplace=True,
    )

    # --------------------------------------------------------
    # 3. Keep required columns
    # --------------------------------------------------------

    bank_b = bank_b_data[
        [
            "Account No",
            "Transaction ID",
            "Value Date",
            "Debit Amount",
            "Credit Amount",
            "Transaction Detail",
            "Transaction Time",
        ]
    ].copy()

    # --------------------------------------------------------
    # 4. Extract transaction trace/reference number
    # --------------------------------------------------------

    detail = bank_b["Transaction Detail"].astype(str)

    trace_conditions = [
        detail.str.startswith("FEE"),
        detail.str.startswith("REVERSAL"),
        ~detail.str.startswith("FEE|REVERSAL"),
    ]

    trace_values = [
        # Fee transactions
        detail.str[:40].str.replace(
            " ",
            "",
            regex=False,
        ),

        # Reversal transactions
        detail.str.extract(
            r"(TX\d+)",
            expand=False,
        ),

        # Standard payment transactions
        detail.str.extract(
            r"(PAY-\d+)",
            expand=False,
        ),
    ]

    bank_b["Trace No"] = np.select(
        trace_conditions,
        trace_values,
        default=None,
    )

    # --------------------------------------------------------
    # 5. Standardize data types
    # --------------------------------------------------------

    bank_b = reformat(
        bank_b,
        date_columns=["Value Date"],
        numeric_columns=[
            "Debit Amount",
            "Credit Amount",
        ],
    )

    # Re-create detail after dataframe transformation
    detail = bank_b["Transaction Detail"].astype(str)

    # --------------------------------------------------------
    # 6. Classify transactions
    # --------------------------------------------------------

    # Disbursement
    bank_b_disbursement = bank_b[
        detail.str.contains(
            "DISBURSEMENT",
            case=False,
            na=False,
        )
    ].copy()

    # Repayment
    bank_b_repayment = bank_b[
        detail.str.contains(
            r"PAYMENT.*REPAYMENT|FEE|LATEFEE",
            regex=True,
            case=False,
            na=False,
        )
        &
        ~detail.str.contains(
            r"REVERSAL.*(FEE|LATEFEE)",
            regex=True,
            case=False,
            na=False,
        )
    ].copy()

    # Batch repayment
    bank_b_batch_repayment = bank_b[
        detail.str.contains(
            r"BATCH.*(REPAYMENT|FEE)",
            regex=True,
            case=False,
            na=False,
        )
    ].copy()

    # Other / unidentified transactions
    bank_b_other = bank_b[
        ~detail.str.contains(
            r"""
            PAYMENT.*REPAYMENT
            |FEE
            |LATEFEE
            |DISBURSEMENT
            |BATCH.*REPAYMENT
            |INTERNAL.*TRANSFER
            |ACCOUNT.*TRANSFER
            """,
            regex=True,
            case=False,
            na=False,
        )
    ].copy()

    # --------------------------------------------------------
    # 7. Return processed datasets
    # --------------------------------------------------------

    return {
        "disbursement": bank_b_disbursement,
        "repayment": bank_b_repayment,
        "batch_repayment": bank_b_batch_repayment,
        "other": bank_b_other,
    }