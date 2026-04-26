"""Derived cleaned HTML artifact generation utilities."""

from __future__ import annotations

from bs4 import BeautifulSoup


def sanitize_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html or "", "lxml")
    for tag_name in ("script", "style", "iframe", "object", "embed"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(True):
        attrs_to_remove = [attr for attr in tag.attrs if attr.lower().startswith("on")]
        for attr in attrs_to_remove:
            tag.attrs.pop(attr, None)

    return str(soup)