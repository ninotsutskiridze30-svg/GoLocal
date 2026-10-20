"""Prepare a bounded, correctly oriented image before a vision request."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_INPUT_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 24_000_000
MAX_SIDE = 1024


class InvalidPosterImage(ValueError):
    """The upload is too large, invalid, or not a supported still image."""


def downscale(image_bytes: bytes) -> bytes:
    """Return an EXIF-corrected JPEG no larger than 1024 px on either side."""
    if not image_bytes or len(image_bytes) > MAX_INPUT_BYTES:
        raise InvalidPosterImage("Image must be between 1 byte and 10 MB")
    try:
        with Image.open(BytesIO(image_bytes)) as opened:
            if opened.format not in {"JPEG", "PNG", "WEBP"}:
                raise InvalidPosterImage("Use a JPEG, PNG, or WebP image")
            if opened.width * opened.height > MAX_PIXELS:
                raise InvalidPosterImage("Image dimensions are too large")
            image = ImageOps.exif_transpose(opened).convert("RGB")
            image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()
    except InvalidPosterImage:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise InvalidPosterImage("Image could not be decoded") from exc
