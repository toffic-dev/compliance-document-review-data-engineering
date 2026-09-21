import os
import requests


BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN", "")


def retrieve_document_file(document_id):
    """
    Fetch the original uploaded document from the Backend.
    """

    url = f"{BACKEND_URL}/api/v1/documents/{document_id}/file"

    headers = {}

    if INTERNAL_SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {INTERNAL_SERVICE_TOKEN}"

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return (
        response.content,
        response.headers.get("content-type", ""),
    )


if __name__ == "__main__":
    file_bytes, content_type = retrieve_document_file(3)

    print(f"Retrieved {len(file_bytes)} bytes")
    print(f"Content-Type: {content_type}")