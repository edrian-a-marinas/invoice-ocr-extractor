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
NEEDS_REVIEW_DIR = Path("data/needs_review")
FAILED_DIR = Path("data/failed")
EXCEL_OUTPUT_PATH = Path("data/output/Invoice_Extract.xlsx")
REVIEW_LOG_PATH = Path("data/output/review_log.csv")


def _move_file(pdf_file: Path, destination_dir: Path) -> None:
    destination = destination_dir / pdf_file.name
    if destination.exists():
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        destination = destination_dir / f"{pdf_file.stem}_{timestamp}{pdf_file.suffix}"
    shutil.move(str(pdf_file), str(destination))
    logger.info(f"[SYSTEM] Moved {pdf_file.name} to {destination}")


def main():
    all_records = []
    all_log_entries = []
    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))
    non_pdf_files = sorted(
        f for f in INPUT_DIR.iterdir() if f.is_file() and f.suffix.lower() != ".pdf"
    )

    for non_pdf_file in non_pdf_files:
        logger.error(
            f"[SYSTEM] {non_pdf_file.name} is not a PDF. Moving to {FAILED_DIR}."
        )
        _move_file(non_pdf_file, FAILED_DIR)

    if not pdf_files and not non_pdf_files:
        logger.info(f"[SYSTEM] No files found in {INPUT_DIR}. Nothing to process.")
    failed_files = len(non_pdf_files)
    needs_review_files = 0
    for pdf_file in pdf_files:
        try:
            records, log_entries = process_pdf(str(pdf_file))
        except Exception as e:
            logger.error(
                f"[SYSTEM] Failed to process {pdf_file.name}: {e}. Moving to {FAILED_DIR}."
            )
            failed_files += 1
            _move_file(pdf_file, FAILED_DIR)
            continue
        all_records.extend(records)
        all_log_entries.extend(log_entries)
        flagged = sum(1 for entry in log_entries if entry.needs_review)
        logger.info(
            f"[SYSTEM] Processed {pdf_file.name}: {len(records)} page(s) | {flagged} flagged for review"
        )
        if flagged > 0:
            needs_review_files += 1
            _move_file(pdf_file, NEEDS_REVIEW_DIR)
        else:
            _move_file(pdf_file, PROCESSED_DIR)
    write_records_to_excel(all_records, str(EXCEL_OUTPUT_PATH))
    write_review_log(all_log_entries, str(REVIEW_LOG_PATH))
    total_flagged = sum(1 for entry in all_log_entries if entry.needs_review)
    logger.info(
        f"[SYSTEM] Run complete: {len(all_log_entries)} page(s) processed | "
        f"{total_flagged} flagged for review | {needs_review_files} file(s) moved to needs_review | "
        f"{failed_files} file(s) moved to failed | "
        f"output written to {EXCEL_OUTPUT_PATH} and {REVIEW_LOG_PATH}"
    )


if __name__ == "__main__":
    main()
