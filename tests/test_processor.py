from types import SimpleNamespace

from app.core.processor import _validate_fields, _check_consistency


def _make_extracted(**overrides):
    """Builds a fake extracted-fields object with sensible valid defaults,
    overridden per test case. Using SimpleNamespace instead of the real
    ExtractedReceiptFields model keeps these tests decoupled from Gemini."""
    defaults = dict(
        receipt_no="OR-65116",
        doctor_name="Dr. Graciano Lopez Jaena",
        prc_license="PRC Lic. No. 00010",
        hospital="QUIRINO MEMORIAL MEDICAL CENTER",
        date="August 25, 2024",
        patient_name="Natividad Soriano Reyes",
        total_amount=3900.0,
        signature_present=True,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestValidateFields:
    def test_valid_record_has_no_issues(self):
        extracted = _make_extracted()
        assert _validate_fields(extracted) == []

    def test_invalid_receipt_no_format(self):
        extracted = _make_extracted(receipt_no="65116")  # missing OR- prefix
        issues = _validate_fields(extracted)
        assert "receipt_no format invalid" in issues

    def test_invalid_prc_license_format(self):
        extracted = _make_extracted(prc_license="00010")  # missing prefix
        issues = _validate_fields(extracted)
        assert "prc_license format invalid" in issues

    def test_prc_license_all_zeros_flagged_as_suspicious(self):
        extracted = _make_extracted(prc_license="PRC Lic. No. 00000")
        issues = _validate_fields(extracted)
        assert "prc_license suspicious (all zeros)" in issues

    def test_invalid_date_format(self):
        extracted = _make_extracted(date="2024/08/25")  # not in DATE_FORMATS
        issues = _validate_fields(extracted)
        assert "date format invalid" in issues

    def test_valid_alternate_date_formats_accepted(self):
        for date_value in ["2024-08-25", "08/25/2024", "Aug 25, 2024"]:
            extracted = _make_extracted(date=date_value)
            issues = _validate_fields(extracted)
            assert "date format invalid" not in issues

    def test_zero_total_amount_flagged(self):
        extracted = _make_extracted(total_amount=0.0)
        issues = _validate_fields(extracted)
        assert "total_amount is zero or negative" in issues

    def test_negative_total_amount_flagged(self):
        extracted = _make_extracted(total_amount=-100.0)
        issues = _validate_fields(extracted)
        assert "total_amount is zero or negative" in issues

    def test_multiple_issues_all_reported(self):
        extracted = _make_extracted(
            receipt_no="bad",
            prc_license="bad",
            date="not-a-date",
            total_amount=0.0,
        )
        issues = _validate_fields(extracted)
        assert len(issues) == 4


class TestCheckConsistency:
    def test_identical_passes_have_no_mismatches(self):
        first = _make_extracted()
        second = _make_extracted()
        assert _check_consistency(first, second) == []

    def test_single_field_mismatch_detected(self):
        first = _make_extracted(prc_license="PRC Lic. No. 00010")
        second = _make_extracted(prc_license="PRC Lic. No. 00000")
        mismatches = _check_consistency(first, second)
        assert mismatches == ["prc_license"]

    def test_multiple_field_mismatches_detected(self):
        first = _make_extracted(receipt_no="OR-65116", total_amount=3900.0)
        second = _make_extracted(receipt_no="OR-61017", total_amount=2350.0)
        mismatches = _check_consistency(first, second)
        assert "receipt_no" in mismatches
        assert "total_amount" in mismatches
        assert len(mismatches) == 2

    def test_signature_present_not_compared(self):
        """signature_present is intentionally excluded from COMPARED_FIELDS."""
        first = _make_extracted(signature_present=True)
        second = _make_extracted(signature_present=False)
        assert _check_consistency(first, second) == []