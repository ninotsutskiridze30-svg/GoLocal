"""Image preparation must constrain input and preserve readable orientation."""

from io import BytesIO

import pytest
from PIL import Image

from golocal_data.poster_images import InvalidPosterImage, downscale


def test_downscale_bounds_longest_side_and_returns_jpeg():
    source = BytesIO()
    Image.new("RGB", (1800, 600), "white").save(source, format="PNG")
    result = downscale(source.getvalue())
    with Image.open(BytesIO(result)) as image:
        assert image.format == "JPEG"
        assert image.size == (1024, 341)


def test_exif_orientation_is_applied_before_resize():
    source = BytesIO()
    image = Image.new("RGB", (120, 60), "white")
    exif = image.getexif()
    exif[274] = 6
    image.save(source, format="JPEG", exif=exif)
    with Image.open(BytesIO(downscale(source.getvalue()))) as prepared:
        assert prepared.size == (60, 120)


@pytest.mark.parametrize("payload", [
    pytest.param(b"", id="empty"),
    pytest.param(b"not an image", id="invalid"),
    pytest.param(b"x" * (10 * 1024 * 1024 + 1), id="oversized"),
])
def test_invalid_input_is_rejected_before_model(payload):
    with pytest.raises(InvalidPosterImage):
        downscale(payload)
