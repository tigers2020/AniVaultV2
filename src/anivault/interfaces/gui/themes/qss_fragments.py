"""Small helpers for assembling QSS blocks."""

from __future__ import annotations


def qss_block(selector: str, *rules: str) -> str:
    """Render a single selector block from declaration lines."""

    normalized = [rule.strip().rstrip(";") + ";" for rule in rules if rule.strip()]
    body = "\n            ".join(normalized)
    return f"{selector} {{\n            {body}\n        }}"


def qss_blocks(*blocks: str) -> str:
    """Join QSS blocks while skipping empty fragments."""

    return "\n        ".join(block for block in blocks if block)
