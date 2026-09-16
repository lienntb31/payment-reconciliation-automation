
import os
import requests
from requests_toolbelt import MultipartEncoder

import warnings
warnings.filterwarnings("ignore")

# 3. Data Ingestion via API: Upload CSV files to GCP DataHub and ingest them into SQL tables

def upload_file(
    api_endpoint: str,
    ingestion_token: str,
    file_path: str,
    parent_dir: str,
) -> requests.Response | None:
    """
    Upload a file to a data-ingestion API using multipart/form-data.

    MultipartEncoder is used to support large file uploads.

    Parameters
    ----------
    api_endpoint : str
        Data-ingestion API endpoint.
    ingestion_token : str
        Authentication token for the ingestion API.
    file_path : str
        Path to the file to upload.
    parent_dir : str
        Destination directory on the ingestion system.

    Returns
    -------
    requests.Response or None
        API response if the file exists; otherwise None.
    """

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, "rb") as file:
            multipart_data = MultipartEncoder(
                fields={
                    "file": (
                        os.path.basename(file_path),
                        file,
                        "text/plain",
                    ),
                    "parent_dir": parent_dir,
                }
            )

            headers = {
                "data-ingestion-token": ingestion_token,
                "Content-Type": multipart_data.content_type,
            }

            response = requests.post(
                api_endpoint,
                headers=headers,
                data=multipart_data,
                timeout=300,
            )

        response.raise_for_status()

        print(
            f"File uploaded successfully: "
            f"{os.path.basename(file_path)}"
        )

        return response

    except requests.RequestException as error:
        print(
            f"Upload failed for {file_path}: {error}"
        )
        return None