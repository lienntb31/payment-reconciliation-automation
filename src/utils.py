from pathlib import Path
from glob import glob

import pandas as pd


def get_source_files(folder, file_prefix):
    """
    Get source files matching a given filename prefix.

    Temporary Excel files created by Microsoft Office (~$)
    are excluded.
    """

    folder = Path(folder)

    return [
        Path(file)
        for file in glob(str(folder / f"{file_prefix}*"))
        if "~$" not in file
    ]


def df_skip_header(
    filepath,
    keyword,
    sheet=0,
    col_idx=0,
    encoding="latin-1",
):
    """
    Read a CSV or Excel file where the actual header
    starts after a variable number of rows.

    Parameters
    ----------
    filepath : str or Path
        Input file path.

    keyword : str
        Value used to identify the actual header row.

    sheet : int or str
        Excel sheet to read.

    col_idx : int
        Column index where the header keyword is expected.

    encoding : str
        Encoding used for CSV files.

    Returns
    -------
    pandas.DataFrame
        Data with standardized column names.
    """

    filepath = Path(filepath)

    if filepath.suffix.lower() == ".csv":

        raw = pd.read_csv(
            filepath,
            header=None,
            encoding=encoding,
        )

    elif filepath.suffix.lower() in [".xlsx", ".xls"]:

        raw = pd.read_excel(
            filepath,
            sheet_name=sheet,
            header=None,
        )

    else:
        raise ValueError(
            f"Unsupported file format: {filepath.suffix}"
        )

    # Find the row containing the actual header
    header_rows = raw.index[
        raw.iloc[:, col_idx]
        .astype(str)
        .str.strip()
        .eq(keyword)
    ].tolist()

    if not header_rows:
        raise ValueError(
            f"Header keyword '{keyword}' "
            f"not found in {filepath.name}"
        )

    header_idx = header_rows[0]

    # Extract data below the header
    data = raw.iloc[header_idx + 1:].copy()

    # Use the detected header as column names
    data.columns = raw.iloc[header_idx].tolist()

    # Remove completely empty rows
    data = data.dropna(
        how="all"
    )

    return data.reset_index(drop=True)


def reformat(
    df,
    date_columns=None,
    numeric_columns=None,
):
    """
    Standardize date and numeric columns.
    """

    date_columns = date_columns or []
    numeric_columns = numeric_columns or []

    df = df.copy()

    # Standardize dates
    for column in date_columns:

        if column in df.columns:
            df[column] = (
                pd.to_datetime(
                    df[column],
                    dayfirst=True,
                    errors="coerce",
                )
                .dt.date
            )

    # Standardize numeric values
    for column in numeric_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            ).fillna(0)

    return df