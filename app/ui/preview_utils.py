"""Artifact preview utilities for local storage display."""

import base64
from pathlib import Path
from typing import Optional, Tuple


def render_html_preview(html_content: str, max_length: int = 50000) -> str:
    """Render HTML preview with safety checks.
    
    Args:
        html_content: Raw HTML bytes
        max_length: Max characters to display (prevent huge files)
    
    Returns:
        Safe HTML string for display
    """
    if not html_content:
        return "<p>Empty HTML document</p>"
    
    if len(html_content) > max_length:
        return f"<p>HTML preview truncated ({len(html_content)} bytes, showing first {max_length}):</p><pre>{html_content[:max_length]}...</pre>"
    
    # Basic XSS prevention: strip dangerous tags
    dangerous_tags = ['<script', '<iframe', '<object', '<embed', 'javascript:', 'onerror=']
    safe_html = html_content
    
    for tag in dangerous_tags:
        safe_html = safe_html.replace(tag, f"&lt;{tag[1:]}")
    
    return safe_html


def render_pdf_preview(pdf_bytes: bytes, max_display: str = "preview") -> str:
    """Generate PDF preview display.
    
    Args:
        pdf_bytes: Raw PDF bytes
        max_display: "preview" | "info" | "base64"
    
    Returns:
        Display string or base64 data
    """
    if not pdf_bytes:
        return "Empty PDF document"
    
    file_size_mb = len(pdf_bytes) / (1024 * 1024)
    
    if max_display == "info":
        return f"PDF Document ({file_size_mb:.2f} MB) - local preview available"
    
    if max_display == "base64":
        return f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}"
    
    # preview mode
    if file_size_mb > 10:
        return f"PDF too large ({file_size_mb:.2f} MB) for browser preview. Download recommended."
    
    return f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}"


def render_text_preview(text_content: str, max_lines: int = 100) -> str:
    """Render text preview.
    
    Args:
        text_content: Text bytes or string
        max_lines: Maximum lines to show
    
    Returns:
        Text display string
    """
    if not text_content:
        return "(empty file)"
    
    lines = text_content.split('\n')
    
    if len(lines) > max_lines:
        return '\n'.join(lines[:max_lines]) + f"\n\n[... truncated {len(lines) - max_lines} lines ...]"
    
    return text_content


def get_preview_mime_type(artifact_type: str) -> str:
    """Get appropriate MIME type for preview.
    
    Args:
        artifact_type: Type from SourceArtifact (html, pdf, json, txt)
    
    Returns:
        MIME type string
    """
    mime_map = {
        "html": "text/html",
        "pdf": "application/pdf",
        "json": "application/json",
        "text": "text/plain",
        "txt": "text/plain",
        "xml": "text/xml",
    }
    return mime_map.get(artifact_type, "text/plain")


def validate_preview_safe(artifact_type: str, content: bytes) -> Tuple[bool, Optional[str]]:
    """Validate that artifact is safe to preview.
    
    Args:
        artifact_type: Type of artifact
        content: Raw bytes
    
    Returns:
        (is_safe, error_message_if_not_safe)
    """
    if not content:
        return False, "Empty content"
    
    max_size_mb = {
        "html": 20,
        "pdf": 50,
        "json": 10,
        "text": 20,
    }
    
    max_bytes = max_size_mb.get(artifact_type, 20) * 1024 * 1024
    
    if len(content) > max_bytes:
        return False, f"File too large ({len(content) / (1024*1024):.1f} MB, max {max_size_mb.get(artifact_type, 20)} MB)"
    
    # Check for binary content in text types
    if artifact_type in ["html", "json", "text"]:
        try:
            content.decode('utf-8')
        except UnicodeDecodeError:
            return False, "File contains binary data, text preview not available"
    
    return True, None
