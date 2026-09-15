from pathlib import Path


def export_results(
    results,
    output_dir,
    file_prefix,
):
    """
    Export processed transaction datasets to CSV files.

    Parameters
    ----------
    results : dict
        Dictionary containing transaction type and DataFrame.
        Example:
        {
            "disbursement": df,
            "repayment": df,
            "other": df
        }

    output_dir : str or Path
        Directory where output files will be saved.

    file_prefix : str
        Prefix used for output filenames.

    Returns
    -------
    list[Path]
        Paths of successfully exported files.
    """

    if not results:
        print("No results to export.")
        return []

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exported_files = []

    for transaction_type, df in results.items():

        if df is None or df.empty:
            continue

        output_file = (
            output_dir
            / f"{file_prefix}_{transaction_type}.csv"
        )

        df.to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig",
        )

        exported_files.append(output_file)

        print(
            f"Exported {transaction_type}: "
            f"{len(df):,} rows -> {output_file}"
        )

    return exported_files