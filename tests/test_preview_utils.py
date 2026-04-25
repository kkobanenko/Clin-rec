"""Tests for preview utilities."""

from app.ui.preview_utils import (
    render_html_preview,
    get_preview_mime_type,
    validate_preview_safe,
)


def test_html_preview_renders():
    """Test HTML preview generation."""
    html = "<html><body>Test</body></html>"
    result = render_html_preview(html)
    assert "Test" in result


def test_mime_type_mapping():
    """Test MIME type mapping."""
    assert get_preview_mime_type("html") == "text/html"
    assert get_preview_mime_type("pdf") == "application/pdf"
    assert get_preview_mime_type("json") == "application/json"


def test_preview_safety_check():
    """Test preview safety validation."""
    content = b"Safe text content"
    is_safe, error = validate_preview_safe("text", content)
    assert is_safe
    assert error is None


def test_empty_content_not_safe():
    """Test that empty content is not safe for preview."""
    content = b""
    is_safe, error = validate_preview_safe("text", content)
    assert not is_safe
    assert "Empty" in error
