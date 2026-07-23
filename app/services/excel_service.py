import openpyxl
from app.core.schemas import ReceiptRecord

HEADERS = [
    "Page", "Receipt No.", "Doctor Name", "PRC License",
    "Hospital", "Date", "Patient Name", "Total Amount (PHP)", "Signature"
]


def write_records_to_excel(records: list[ReceiptRecord], output_path: str) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active

    for col, header in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = openpyxl.styles.Font(bold=True)

    for row_idx, record in enumerate(records, start=2):
        ws.cell(row=row_idx, column=1, value=record.page)
        ws.cell(row=row_idx, column=2, value=record.receipt_no)
        ws.cell(row=row_idx, column=3, value=record.doctor_name)
        ws.cell(row=row_idx, column=4, value=record.prc_license)
        ws.cell(row=row_idx, column=5, value=record.hospital)
        ws.cell(row=row_idx, column=6, value=record.date)
        ws.cell(row=row_idx, column=7, value=record.patient_name)

        amount_cell = ws.cell(row=row_idx, column=8, value=record.total_amount)
        amount_cell.number_format = '"PHP "#,##0.00'

        ws.cell(row=row_idx, column=9, value=record.signature)

    wb.save(output_path)