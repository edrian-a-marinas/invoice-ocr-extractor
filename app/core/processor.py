import logging
from pathlib import Path
from app.services.pdf_service import convert_pdf_to_images
from app.services.gemini_extraction_service import extract_receipt_fields
from app.core.schemas import ReceiptRecord, ReviewLogEntry
import re
from datetime import datetime

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = [
    "receipt_no",
    "doctor_name",
    "prc_license",
    "hospital",
    "date",
    "patient_name",
]

DATE_FORMATS = ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]


def _validate_fields(extracted) -> list[str]:
    """Deterministic business-rule checks, independent of any model self-reported confidence.
    Rules are intentionally generic so they hold for receipts beyond today's sample set.
    """
    issues = []

    if not re.fullmatch(r"[A-Z]{0,4}-?\d{3,}", extracted.receipt_no):
        issues.append("receipt_no format invalid")

    prc_match = re.fullmatch(r"PRC Lic\. No\. (\d{4,6})", extracted.prc_license)
    if not prc_match:
        issues.append("prc_license format invalid")
    elif re.fullmatch(r"0+", prc_match.group(1)):
        issues.append("prc_license suspicious (all zeros)")

    if not any(_try_parse_date(extracted.date, fmt) for fmt in DATE_FORMATS):
        issues.append("date format invalid")

    if extracted.total_amount <= 0:
        issues.append("total_amount is zero or negative")

    return issues


def _try_parse_date(value: str, fmt: str) -> bool:
    try:
        datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


COMPARED_FIELDS = [
    "receipt_no",
    "doctor_name",
    "prc_license",
    "hospital",
    "date",
    "patient_name",
    "total_amount",
]


def _check_consistency(first, second) -> list[str]:
    """Runs extraction twice and flags fields that disagree between passes.
    Disagreement is direct evidence of ambiguity in the source image."""
    mismatches = []
    for field in COMPARED_FIELDS:
        if getattr(first, field) != getattr(second, field):
            mismatches.append(field)
    return mismatches


def _process_page(
    image, page_num: int, file_name: str
) -> tuple[ReceiptRecord, ReviewLogEntry]:
    extracted = extract_receipt_fields(image)
    second_pass = extract_receipt_fields(image)
    inconsistent_fields = _check_consistency(extracted, second_pass)

    empty_fields = [
        field for field in REQUIRED_FIELDS if not getattr(extracted, field).strip()
    ]
    unreadable_fields = [
        field
        for field in REQUIRED_FIELDS
        if getattr(extracted, field).strip() == "UNREADABLE"
    ]
    if extracted.total_amount == -1:
        unreadable_fields.append("total_amount")
    validation_issues = _validate_fields(extracted)
    all_issues = empty_fields + unreadable_fields + validation_issues
    if inconsistent_fields:
        all_issues.append(
            f"Inconsistent across passes (verify entire row): {', '.join(inconsistent_fields)}"
        )

    needs_review = bool(all_issues)
    if needs_review:
        logger.warning(
            f"[SYSTEM] {file_name} page {page_num} issues: {', '.join(all_issues)}"
        )

    record = ReceiptRecord(
        page=page_num,
        receipt_no=extracted.receipt_no,
        doctor_name=extracted.doctor_name,
        prc_license=extracted.prc_license,
        hospital=extracted.hospital,
        date=extracted.date,
        patient_name=extracted.patient_name,
        total_amount=extracted.total_amount,
        signature="Yes" if extracted.signature_present else "No",
    )

    log_entry = ReviewLogEntry(
        file_name=file_name,
        page=page_num,
        needs_review=needs_review,
        remarks=", ".join(all_issues) if all_issues else "",
    )

    return record, log_entry


def process_pdf(pdf_path: str) -> tuple[list[ReceiptRecord], list[ReviewLogEntry]]:
    file_name = Path(pdf_path).name
    images = convert_pdf_to_images(pdf_path)
    records = []
    log_entries = []
    for page_num, image in enumerate(images, start=1):
        record, log_entry = _process_page(image, page_num, file_name)
        records.append(record)
        log_entries.append(log_entry)
    return records, log_entries
