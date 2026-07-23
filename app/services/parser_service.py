import re
from app.core.schemas import ReceiptRecord


def parse_receipt_text(text: str, page: int) -> tuple[ReceiptRecord, list[str]]:
    fields = {
        "Receipt No.": _extract(r"OR[-\s]?No\.?\s*[:\-]?\s*(OR-?\d+)", text),
        "Doctor Name": _extract(r"Dr\.\s*([A-Za-z\s.]+?)(?=\n|Neurology|Cardiology|Pediatrics|$)", text),
        "PRC License": _extract(r"(PRC\s*Lic\.?\s*No\.?\s*\d+)", text),
        "Hospital": _extract(r"^([A-Z\s]+MEDICAL CENTER|[A-Z\s]+HOSPITAL)", text),
        "Date": _extract(r"Date[:\s]*([A-Za-z]+\s\d{1,2},\s\d{4})", text),
        "Patient Name": _extract(r"Patient[:\s]*([A-Za-z\s]+?)(?=\n|$)", text),
        "Total Amount": _extract(r"PHP\s*([\d,]+\.\d{2})", text),
    }

    empty_fields = [name for name, value in fields.items() if not value.strip()]

    signature_detected = "Yes" if re.search(r"Attending Physician", text) else "No"

    record = ReceiptRecord(
        page=page,
        receipt_no=fields["Receipt No."],
        doctor_name=fields["Doctor Name"].strip(),
        prc_license=fields["PRC License"],
        hospital=fields["Hospital"].strip(),
        date=fields["Date"],
        patient_name=fields["Patient Name"].strip(),
        total_amount=float(fields["Total Amount"].replace(",", "")) if fields["Total Amount"] else 0.0,
        signature=signature_detected,
    )

    return record, empty_fields


def _extract(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    return match.group(1) if match else ""