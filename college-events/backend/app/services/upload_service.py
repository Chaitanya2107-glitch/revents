import warnings
from io import BytesIO
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.errors import fail


def upload_poster(file: UploadFile) -> str:
    settings = get_settings()
    maximum = settings.max_upload_size_mb * 1024 * 1024
    content = file.file.read(maximum + 1)
    if len(content) > maximum:
        fail(413, "UPLOAD_TOO_LARGE", "Poster exceeds the configured upload size limit.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    fail(422, "INVALID_POSTER", "Use a valid JPEG, PNG, or WebP image.")
                if image.width * image.height > settings.max_image_pixels:
                    fail(413, "IMAGE_TOO_LARGE", "Poster exceeds the configured pixel limit.")
                image.verify()
            with Image.open(BytesIO(content)) as image:
                image.load()
                # Re-encode decoded pixels to remove appended content and untrusted metadata.
                safe_image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
                output = BytesIO()
                safe_image.save(output, format="WEBP", quality=85, method=4)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning):
        fail(422, "INVALID_POSTER", "Poster could not be decoded as a safe image.")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.webp"
    (settings.upload_dir / filename).write_bytes(output.getvalue())
    return f"{settings.public_base_url.rstrip('/')}/uploads/{filename}"
