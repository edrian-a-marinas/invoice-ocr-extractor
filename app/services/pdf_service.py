from pdf2image import convert_from_path
from PIL import Image


def convert_pdf_to_images(pdf_path: str, dpi: int = 300) -> list[Image.Image]:
    images = convert_from_path(pdf_path, dpi=dpi)
    return images