import logging
from pathlib import Path
from app.services.pdf_service import convert_pdf_to_images
from app.services.image_preprocessing_service import deskew_image, enhance_image
from app.services.ocr_service import extract_text_with_confidence
from app.services.parser_service import parse_receipt_text
from app.core.schemas import ReceiptRecord, ReviewLogEntry

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 95.0  # below this = flagged for review with remarks.


def _process_page(image, page_num: int, file_name: str) -> tuple[ReceiptRecord, dict]:
    processed = deskew_image(image)
    processed = enhance_image(processed)

    text, confidence = extract_text_with_confidence(processed)

    if confidence < CONFIDENCE_THRESHOLD:
        logger.warning(f"[SYSTEM] {file_name} page {page_num} low OCR confidence ({confidence:.1f}%), retrying")
        text, confidence = extract_text_with_confidence(processed)

    needs_review = confidence < CONFIDENCE_THRESHOLD

    record, empty_fields = parse_receipt_text(text, page_num)

    if needs_review:
        logger.warning(f"[SYSTEM] {file_name} page {page_num} still low confidence ({confidence:.1f}%) after retry, flagged")
        remarks = f"Field extraction failed: {', '.join(empty_fields)}" if empty_fields else "Low OCR confidence"
    else:
        remarks = ""

    log_entry = ReviewLogEntry(
        file_name=file_name,
        page=page_num,
        needs_review=needs_review,
        confidence_score=round(confidence, 1),
        remarks=remarks,
    )

    return record, log_entry

def process_pdf(pdf_path: str) -> tuple[list[ReceiptRecord], list[dict]]:
    file_name = Path(pdf_path).name
    images = convert_pdf_to_images(pdf_path)
    records = []
    log_entries = []

    for page_num, image in enumerate(images, start=1):
        record, log_entry = _process_page(image, page_num, file_name)
        records.append(record)
        log_entries.append(log_entry)

    return records, log_entries