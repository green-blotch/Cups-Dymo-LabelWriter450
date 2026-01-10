"""Tests for label_generator module aligned to Acceptance_Tests.md."""

import pytest
from PIL import Image

from cups_dymo_label_printer.label_generator import create_label_image
from cups_dymo_label_printer.config import LABEL_SIZES, DEFAULT_DPI


class TestLabelGenerator:
    def test_render_default_label_dimensions_and_background(self):
        # Given
        text = "Hello World"

        # When
        image = create_label_image(text)

        # Then
        assert isinstance(image, Image.Image)
        size_info = LABEL_SIZES['11354']
        expected_width = int(size_info['width_mm'] * DEFAULT_DPI / 25.4)
        expected_height = int(size_info['height_mm'] * DEFAULT_DPI / 25.4)
        assert image.size == (expected_width, expected_height)
        assert image.mode == 'RGB'
        assert image.getpixel((0, 0)) == (255, 255, 255)

    @pytest.mark.parametrize(
        "label_code,expected_cups",
        [
            ("11354", "w162h90"),
            ("30252", "w79h252"),
            ("30323", "w153h286"),
            ("30256", "w167h286"),
            ("99012", "w252h102"),
        ],
    )
    def test_support_all_configured_label_sizes(self, label_code, expected_cups):
        # Given
        text = "Test"

        # When
        image = create_label_image(text, label_size=label_code)

        # Then
        size_info = LABEL_SIZES[label_code]
        expected_width = int(size_info['width_mm'] * DEFAULT_DPI / 25.4)
        expected_height = int(size_info['height_mm'] * DEFAULT_DPI / 25.4)
        assert image.size == (expected_width, expected_height)
        assert size_info['cups'] == expected_cups

    def test_reject_unknown_label_size(self):
        # Given
        text = "Test"

        # When / Then
        with pytest.raises(ValueError) as exc_info:
            create_label_image(text, label_size="INVALID")

        assert "Unknown label size: INVALID" in str(exc_info.value)

    @pytest.mark.parametrize("align", ["left", "center", "right"])
    def test_align_text_within_bounds(self, align):
        # Given
        text = "Align Me"

        # When
        image = create_label_image(text, align=align)

        # Then
        bbox = image.getbbox()
        # Text is black on white, so bbox must exist and be within image bounds
        assert bbox is not None
        left, upper, right, lower = bbox
        assert 0 <= left < right <= image.width
        assert 0 <= upper < lower <= image.height
