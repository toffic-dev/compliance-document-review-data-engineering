from io import BytesIO

import pdfplumber
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from rule_lookup import find_matching_rules
from disclosure_check import check_disclosure
from precedent_search import find_precedents
from retrieve_document import retrieve_document_file


app = FastAPI()


# ---------------------------------------------------------
# Request models
# ---------------------------------------------------------

class TextQuery(BaseModel):
    text: str


class DisclosureQuery(BaseModel):
    document_chunks: list[str]
    disclosure_id: str
    disclosure_text: str


# ---------------------------------------------------------
# Existing Data Engineering endpoints
# ---------------------------------------------------------

@app.post("/rule-lookup")
def rule_lookup_endpoint(query: TextQuery):
    return find_matching_rules(query.text)


@app.post("/disclosure-check")
def disclosure_check_endpoint(query: DisclosureQuery):
    return check_disclosure(
        query.document_chunks,
        query.disclosure_id,
        query.disclosure_text,
    )


@app.post("/precedent-search")
def precedent_search_endpoint(query: TextQuery):
    return find_precedents(query.text)


# ---------------------------------------------------------
# Document extraction endpoint
# ---------------------------------------------------------

@app.get("/documents/{document_id}/extracted-text")
def extracted_text_endpoint(document_id: int):
    """
    Retrieve an uploaded document from the Backend
    and extract its text.
    """

    # Retrieve document from Backend
    try:
        file_bytes, content_type = retrieve_document_file(document_id)

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve document from Backend",
        ) from exc

    # Extract PDF text
    try:
        if (
            content_type == "application/pdf"
            or file_bytes.startswith(b"%PDF")
        ):
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:

                text_parts = []

                for page in pdf.pages:
                    page_text = page.extract_text()

                    if page_text:
                        text_parts.append(page_text)

                extracted_text = "\n".join(text_parts)

        else:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported document type: {content_type}",
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to extract text from document",
        ) from exc

    # Make sure something was actually extracted
    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from document",
        )

    return {
        "document_id": document_id,
        "extracted_text": extracted_text,
    }