import logging
from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)


def convert_pdf_to_images(pdf_path: str, dpi: int = 300) -> list[Image.Image]:
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        return images
    except Exception as e:
        logger.error(
            f"[PDF] Failed to convert {pdf_path} to images (corrupt, password-protected, or not a valid PDF): {e}"
        )
        raise
