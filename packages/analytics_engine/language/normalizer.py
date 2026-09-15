"""Conservative Vietnamese canonicalization without translating to English."""

from __future__ import annotations

import re

from packages.domain import NormalizedQuestion
from packages.shared.text import normalize_vietnamese


class VietnameseNormalizer:
    """Normalize aliases while retaining the original question for evidence."""

    _ALIASES = {
        "mau xe": "dong xe",
        "model xe": "dong xe",
        "diem sac": "tram sac",
        "sac hoan tat": "sac thanh cong",
        "phien sac loi": "sac that bai",
        "tp hcm": "ho chi minh",
        "tphcm": "ho chi minh",
        "sai gon": "ho chi minh",
        "hn": "ha noi",
    }
    _STANDALONE_ALIASES = {
        # Common conversational shorthand. Keep this separate from phrase aliases
        # so an already-canonical "khach hang" never becomes "khach hang hang".
        "khach": "khach hang",
    }

    def normalize(self, question: str) -> NormalizedQuestion:
        normalized = normalize_vietnamese(question)
        canonical = normalized
        matched: list[str] = []
        for alias, replacement in sorted(
            self._ALIASES.items(), key=lambda item: len(item[0]), reverse=True
        ):
            pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
            canonical, count = re.subn(pattern, replacement, canonical)
            if count:
                matched.append(alias)
        for alias, replacement in self._STANDALONE_ALIASES.items():
            canonical_suffix = replacement.removeprefix(alias).strip()
            suffix_guard = (
                rf"(?!\s+{re.escape(canonical_suffix)}\b)"
                if canonical_suffix
                else ""
            )
            pattern = rf"(?<!\w){re.escape(alias)}{suffix_guard}(?!\w)"
            canonical, count = re.subn(pattern, replacement, canonical)
            if count:
                matched.append(alias)
        return NormalizedQuestion(
            original=question,
            normalized=normalized,
            canonical=canonical,
            matched_aliases=matched,
        )
