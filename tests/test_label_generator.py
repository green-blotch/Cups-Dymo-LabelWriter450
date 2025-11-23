"""
Tests for label_generator module.

Tests the creation of label images with various parameters.
No mocking required - these are pure unit tests of PIL image generation.
"""

import pytest
from PIL import Image

from cups_dymo_label_printer.label_generator import create_label_image
from cups_dymo_label_printer.config import LABEL_SIZES, DEFAULT_DPI


class TestLabelGeneratorHappyPath:
    """Happy path tests for label generation."""
    
    def test_create_label_with_default_settings(self):
        """Should create label image with default settings."""
        # Given
        text = "Hello World"
        
        # When
        image = create_label_image(text)
        
        # Then
        assert isinstance(image, Image.Image)
        
        # Check dimensions for label 11354 at 300 DPI
        size_info = LABEL_SIZES['11354']
        expected_width = int(size_info['width_mm'] * DEFAULT_DPI / 25.4)
        expected_height = int(size_info['height_mm'] * DEFAULT_DPI / 25.4)
        
        assert image.width == expected_width
        assert image.height == expected_height
        assert image.mode == 'RGB'
        
        # Check that corners are white (background)
        top_left = image.getpixel((0, 0))
        assert top_left == (255, 255, 255), "Background should be white"
    
    def test_create_label_with_custom_font_size_and_alignment(self):
        """Should create label with custom font size and alignment."""
        # Given
        text = "Test Label"
        font_size = 60
        align = "left"
        
        # When
        image = create_label_image(text, font_size=font_size, align=align)
        
        # Then
        assert isinstance(image, Image.Image)
        
        # We can't easily test exact text position without complex image analysis,
        # but we can verify the image was created successfully
        assert image.width > 0
        assert image.height > 0
    
    def test_create_label_with_right_alignment(self):
        """Should handle right alignment correctly."""
        # Given
        text = "Right Aligned"
        align = "right"
        
        # When
        image = create_label_image(text, align=align)
        
        # Then
        assert isinstance(image, Image.Image)
        # Verify image was created (text positioning is hard to verify without OCR)
        assert image.width > 0
    
    def test_create_label_with_center_alignment(self):
        """Should handle center alignment correctly."""
        # Given
        text = "Centered Text"
        align = "center"
        
        # When
        image = create_label_image(text, align=align)
        
        # Then
        assert isinstance(image, Image.Image)
    
    @pytest.mark.parametrize("label_code,expected_cups", [
        ("11354", "w162h90"),
        ("30252", "w79h252"),
        ("30323", "w153h286"),
        ("30256", "w167h286"),
        ("99012", "w252h102"),
    ])
    def test_support_all_defined_label_sizes(self, label_code, expected_cups):
        """Should support all defined label sizes."""
        # Given
        text = "Test"
        
        # When
        image = create_label_image(text, label_size=label_code)
        
        # Then
        assert isinstance(image, Image.Image)
        
        # Verify dimensions match specifications
        size_info = LABEL_SIZES[label_code]
        expected_width = int(size_info['width_mm'] * DEFAULT_DPI / 25.4)
        expected_height = int(size_info['height_mm'] * DEFAULT_DPI / 25.4)
        
        assert image.width == expected_width
        assert image.height == expected_height
        assert size_info['cups'] == expected_cups


class TestLabelGeneratorErrorCases:
    """Error case tests for label generation."""
    
    def test_raise_value_error_for_unknown_label_size(self):
        """Should raise ValueError for unknown label size."""
        # Given
        text = "Test"
        invalid_label_size = "INVALID"
        
        # When/Then
        with pytest.raises(ValueError) as exc_info:
            create_label_image(text, label_size=invalid_label_size)
        
        assert "Unknown label size: INVALID" in str(exc_info.value)


class TestLabelGeneratorEdgeCases:
    """Edge case tests for label generation."""
    
    def test_create_label_with_empty_text(self):
        """Should create label even with empty text."""
        # Given
        text = ""
        
        # When
        image = create_label_image(text)
        
        # Then
        assert isinstance(image, Image.Image)
        # Should still have correct dimensions
        assert image.width > 0
        assert image.height > 0
    
    def test_create_label_with_very_long_text(self):
        """Should handle very long text (may overflow but shouldn't crash)."""
        # Given
        text = "A" * 1000
        
        # When
        image = create_label_image(text)
        
        # Then
        assert isinstance(image, Image.Image)
    
    def test_create_label_with_minimum_font_size(self):
        """Should create label with minimum font size."""
        # Given
        text = "Small"
        font_size = 10
        
        # When
        image = create_label_image(text, font_size=font_size)
        
        # Then
        assert isinstance(image, Image.Image)
    
    def test_create_label_with_maximum_font_size(self):
        """Should create label with maximum font size."""
        # Given
        text = "Big"
        font_size = 200
        
        # When
        image = create_label_image(text, font_size=font_size)
        
        # Then
        assert isinstance(image, Image.Image)
    
    def test_create_label_with_multiline_text(self):
        """Should handle multiline text."""
        # Given
        text = "Line 1\nLine 2\nLine 3"
        
        # When
        image = create_label_image(text)
        
        # Then
        assert isinstance(image, Image.Image)
    
    def test_create_label_with_special_characters(self):
        """Should handle special characters."""
        # Given
        text = "Hello! @#$%^&*() <> {} []"
        
        # When
        image = create_label_image(text)
        
        # Then
        assert isinstance(image, Image.Image)
