import os
import csv
from app.core.schemas import ReviewLogEntry


def write_review_log(entries: list[ReviewLogEntry], output_path: str) -> None:
    headers = ["File Name", "Page", "Needs Review", "Remarks"]
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "File Name": entry.file_name,
                    "Page": entry.page,
                    "Needs Review": "Yes" if entry.needs_review else "No",
                    "Remarks": entry.remarks,
                }
            )
