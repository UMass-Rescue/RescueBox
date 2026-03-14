"""
Unit tests for text area height calculation utility function.

Tests the calculate_text_area_height function that dynamically
determines appropriate CSS height classes based on text length.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the function directly
from frontend.chatbot.utils import calculate_text_area_height


def test_calculate_text_area_height_short_text():
    """Test height calculation for short text."""
    result = calculate_text_area_height(50)
    assert result == 'h-25', f"Expected 'h-25', got '{result}'"
    print("✓ Short text test passed")


def test_calculate_text_area_height_medium_text():
    """Test height calculation for medium text."""
    result = calculate_text_area_height(300)
    assert result == 'h-75', f"Expected 'h-75', got '{result}'"
    print("✓ Medium text test passed")


def test_calculate_text_area_height_long_text():
    """Test height calculation for long text (Twinkle Twinkle lyrics)."""
    result = calculate_text_area_height(683)  # Length of test lyrics
    assert result == 'h-96', f"Expected 'h-96', got '{result}'"
    print("✓ Long text test passed")


def test_calculate_text_area_height_very_long_text():
    """Test height calculation for very long text (capped at 384px)."""
    result = calculate_text_area_height(2000)
    assert result == 'h-96', f"Expected 'h-96' (capped at 384px), got '{result}'"
    print("✓ Very long text test passed")


def test_calculate_text_area_height_empty_text():
    """Test height calculation for empty text."""
    result = calculate_text_area_height(0)
    assert result == 'h-24', f"Expected 'h-24', got '{result}'"
    print("✓ Empty text test passed")


def test_calculate_text_area_height_edge_cases():
    """Test height calculation edge cases."""
    # Very large text (capped at 384px)
    result = calculate_text_area_height(10000)
    assert result == 'h-96', f"Expected 'h-96' (capped at 384px), got '{result}'"

    # Boundary test (400 chars = h-95 after calculation)
    result = calculate_text_area_height(400)
    assert result == 'h-95', f"Expected 'h-95', got '{result}'"
    print("✓ Edge cases test passed")


if __name__ == "__main__":
    print("Running text area height calculation tests...")
    test_calculate_text_area_height_short_text()
    test_calculate_text_area_height_medium_text()
    test_calculate_text_area_height_long_text()
    test_calculate_text_area_height_very_long_text()
    test_calculate_text_area_height_empty_text()
    test_calculate_text_area_height_edge_cases()
    print("\n🎉 All tests passed!")
