import logging
import shutil
from datetime import datetime
from pathlib import Path
from app.core.processor import process_pdf
from app.services.excel_service import write_records_to_excel
from app.services.review_log_service import write_review_log

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INPUT_DIR = Path("data/input")
PROCESSED_DIR = Path("data/processed")
EXCEL_OUTPUT_PATH = Path("data/output/Invoice_Extract.xlsx")
REVIEW_LOG_PATH = Path("data/output/review_log.csv")


def _move_to_processed(pdf_file: Path) -> None:
    destination = PROCESSED_DIR / pdf_file.name
    if destination.exists():
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        destination = PROCESSED_DIR / f"{pdf_file.stem}_{timestamp}{pdf_file.suffix}"
    shutil.move(str(pdf_file), str(destination))
    logger.info(f"[SYSTEM] Moved {pdf_file.name} to {destination}")


def main():
    all_records = []
    all_log_entries = []
    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        logger.info(f"[SYSTEM] No PDF files found in {INPUT_DIR}. Nothing to process.")

    failed_files = 0

    for pdf_file in pdf_files:
        try:
            records, log_entries = process_pdf(str(pdf_file))
        except Exception as e:
            logger.error(
                f"[SYSTEM] Failed to process {pdf_file.name}: {e}. Skipping, left in input folder."
            )
            failed_files += 1
            continue

        all_records.extend(records)
        all_log_entries.extend(log_entries)
        flagged = sum(1 for entry in log_entries if entry.needs_review)
        logger.info(
            f"[SYSTEM] Processed {pdf_file.name}: {len(records)} page(s) | {flagged} flagged for review"
        )
        _move_to_processed(pdf_file)

    write_records_to_excel(all_records, str(EXCEL_OUTPUT_PATH))
    write_review_log(all_log_entries, str(REVIEW_LOG_PATH))

    total_flagged = sum(1 for entry in all_log_entries if entry.needs_review)
    logger.info(
        f"[SYSTEM] Run complete: {len(all_log_entries)} page(s) processed | "
        f"{total_flagged} flagged for review | {failed_files} file(s) failed | "
        f"output written to {EXCEL_OUTPUT_PATH} and {REVIEW_LOG_PATH}"
    )


if __name__ == "__main__":
    main()
