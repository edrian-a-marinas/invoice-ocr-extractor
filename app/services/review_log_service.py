import csv
from app.core.schemas import ReviewLogEntry


def write_review_log(entries: list[ReviewLogEntry], output_path: str) -> None:
    headers = ["File Name", "Page", "Needs Review", "Confidence Score (%)", "Remarks"]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for entry in entries:
            writer.writerow({
                "File Name": entry.file_name,
                "Page": entry.page,
                "Needs Review": "Yes" if entry.needs_review else "No",
                "Confidence Score (%)": entry.confidence_score,
                "Remarks": entry.remarks,
            })