import csv

from app.core.schemas import ReviewLogEntry
from app.services.review_log_service import write_review_log


def _make_entry(**overrides):
    defaults = dict(
        file_name="doctor_receipts_1.pdf",
        page=1,
        needs_review=False,
        remarks="",
    )
    defaults.update(overrides)
    return ReviewLogEntry(**defaults)


def _read_rows(output_path):
    with open(output_path, newline="") as f:
        return list(csv.DictReader(f))


class TestWriteReviewLog:
    def test_creates_file_with_correct_headers(self, tmp_path):
        output_path = tmp_path / "test.csv"
        write_review_log([_make_entry()], str(output_path))

        with open(output_path, newline="") as f:
            header_line = f.readline().strip()
        assert header_line == "File Name,Page,Needs Review,Remarks"

    def test_needs_review_maps_to_yes_no(self, tmp_path):
        output_path = tmp_path / "test.csv"
        write_review_log(
            [_make_entry(needs_review=True, remarks="prc_license suspicious"),
             _make_entry(needs_review=False)],
            str(output_path),
        )

        rows = _read_rows(output_path)
        assert rows[0]["Needs Review"] == "Yes"
        assert rows[0]["Remarks"] == "prc_license suspicious"
        assert rows[1]["Needs Review"] == "No"
        assert rows[1]["Remarks"] == ""

    def test_second_run_appends_not_overwrites(self, tmp_path):
        output_path = tmp_path / "test.csv"
        write_review_log([_make_entry(file_name="doctor_receipts_1.pdf")], str(output_path))
        write_review_log([_make_entry(file_name="doctor_receipts_2.pdf")], str(output_path))

        rows = _read_rows(output_path)
        assert len(rows) == 2
        assert rows[0]["File Name"] == "doctor_receipts_1.pdf"
        assert rows[1]["File Name"] == "doctor_receipts_2.pdf"

    def test_header_not_duplicated_on_second_run(self, tmp_path):
        output_path = tmp_path / "test.csv"
        write_review_log([_make_entry()], str(output_path))
        write_review_log([_make_entry()], str(output_path))

        with open(output_path, newline="") as f:
            lines = f.readlines()
        header_count = sum(1 for line in lines if line.startswith("File Name,"))
        assert header_count == 1

    def test_empty_entries_on_existing_file_does_not_wipe_data(self, tmp_path):
        output_path = tmp_path / "test.csv"
        write_review_log([_make_entry(file_name="doctor_receipts_1.pdf")], str(output_path))
        write_review_log([], str(output_path))

        rows = _read_rows(output_path)
        assert len(rows) == 1
        assert rows[0]["File Name"] == "doctor_receipts_1.pdf"