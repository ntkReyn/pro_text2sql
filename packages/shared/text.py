"""Deterministic text utilities shared by language and semantic components."""

from __future__ import annotations

import re
import unicodedata


def normalize_vietnamese(value: str) -> str:
    """Return a lowercase, accent-insensitive form used only for matching."""

    decomposed = unicodedata.normalize("NFD", value.casefold())
    without_marks = "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )
    return re.sub(r"\s+", " ", without_marks.replace("đ", "d")).strip()
