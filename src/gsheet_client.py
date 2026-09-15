import gspread

from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client(service_account_file):
    credentials = Credentials.from_service_account_file(
        service_account_file,
        scopes=SCOPES,
    )

    return gspread.authorize(credentials)


def write_dataframe(
    client,
    spreadsheet_name,
    worksheet_name,
    df,
):
    spreadsheet = client.open(spreadsheet_name)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        worksheet.clear()
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=max(len(df) + 10, 100),
            cols=max(len(df.columns) + 5, 20),
        )

    values = [
        df.columns.tolist()
    ] + df.fillna("").astype(str).values.tolist()

    worksheet.update(
        range_name="A1",
        values=values,
    )