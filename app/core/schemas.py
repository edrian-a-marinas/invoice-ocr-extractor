from pydantic import BaseModel
from typing import Literal

# --- Receipt Record (Excel Output) ---------------------------------------------------------
class ReceiptRecord(BaseModel):
    """Used for both parsed OCR data and final Excel export — single source of truth."""
    page: int
    receipt_no: str
    doctor_name: str
    prc_license: str    
    hospital: str
    date: str           
    patient_name: str
    total_amount: float      
    signature: Literal["Yes", "No"]

# --- Review Log Service ---------------------------------------------------------
class ReviewLogEntry(BaseModel):
    file_name: str
    page: int
    needs_review: bool
    confidence_score: float
    remarks: str = ""