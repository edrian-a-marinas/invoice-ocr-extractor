import logging
from google import genai
from app.core.schemas import ExtractedReceiptFields
from PIL import Image
import io
from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.1-flash-lite"

client = genai.Client(api_key=GEMINI_API_KEY)


EXTRACTION_PROMPT = """
Extract the following fields from this medical receipt image:
- receipt_no: the Official Receipt number, formatted exactly as "OR-XXXXX" (include the "OR-" prefix with the dash, but exclude any leading "No." or "No:" text). Example: if the receipt shows "OR No: OR-65116", extract "OR-65116".
- doctor_name: the attending physician's full name
- prc_license: the PRC license, formatted exactly as "PRC Lic. No. XXXXX" (include the full prefix). Example: if the receipt shows "PRC Lic. No 00010", extract "PRC Lic. No. 00010".
- hospital: the hospital or medical center name
- date: the receipt date, in "Month DD, YYYY" format
- patient_name: the patient's full name
- total_amount: the total amount in PHP, as a number (no currency symbol or commas)
- signature_present: true if a handwritten signature appears near "Attending Physician", false otherwise

If a field is not visible or not present, return an empty string for text fields, 0.0 for total_amount, and false for signature_present.

If a field IS present in the image but too blurry, dark, low-resolution, or ambiguous to read with genuine confidence, do NOT guess — return the literal string "UNREADABLE" for that field instead (or -1 for total_amount if the amount itself is unreadable). Only return "UNREADABLE" when you would otherwise be guessing between multiple possible characters/values.
"""


def extract_receipt_fields(image: Image.Image) -> ExtractedReceiptFields:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    try:
        uploaded_file = client.files.upload(
            file=io.BytesIO(image_bytes), config={"mime_type": "image/png"}
        )
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=[
                {"type": "text", "text": EXTRACTION_PROMPT},
                {
                    "type": "image",
                    "uri": uploaded_file.uri,
                    "mime_type": uploaded_file.mime_type,
                },
            ],
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": ExtractedReceiptFields.model_json_schema(),
            },
        )
        return ExtractedReceiptFields.model_validate_json(interaction.output_text)
    except Exception as e:
        logger.error(f"[GEMINI] Extraction API call failed: {e}")
        raise
