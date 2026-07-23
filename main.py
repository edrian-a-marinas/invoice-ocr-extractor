import logging
from pathlib import Path
from app.core.processor import process_pdf
from app.services.excel_service import write_records_to_excel
from app.services.review_log_service import write_review_log

logging.basicConfig(level=logging.INFO)

INPUT_DIR = Path("data/input")
EXCEL_OUTPUT_PATH = Path("data/output/Invoice_Extract.xlsx")
REVIEW_LOG_PATH = Path("data/output/review_log.csv")


def main():
    all_records = []
    all_log_entries = []

    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))
    for pdf_file in pdf_files:
        records, log_entries = process_pdf(str(pdf_file))
        all_records.extend(records)
        all_log_entries.extend(log_entries)

    write_records_to_excel(all_records, str(EXCEL_OUTPUT_PATH))
    write_review_log(all_log_entries, str(REVIEW_LOG_PATH))


if __name__ == "__main__":
    main()
