"""Shared episode and season parsing helpers for GUI models."""

from __future__ import annotations

import re


def extract_episode_numbers(value: str) -> list[int]:
    """Parse an episode field into one or more episode numbers."""

    text = (value or "").strip()
    if not text:
        return []
    range_match = re.fullmatch(r"(\d+)\s*[-~]\s*(\d+)", text)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        if start <= end:
            return list(range(start, end + 1))
        return [start, end]
    if text.isdigit():
        return [int(text)]
    return [int(match) for match in re.findall(r"\d+", text)]


def episode_numbers_to_text(values: list[int]) -> str:
    """Render episode numbers back to a compact text form."""

    numbers: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        numbers.append(value)
    if not numbers:
        return ""
    if len(numbers) == 1:
        return str(numbers[0])
    if numbers == list(range(numbers[0], numbers[-1] + 1)):
        return f"{numbers[0]}-{numbers[-1]}"
    return ",".join(str(value) for value in numbers)


def extract_first_season_number(value: str) -> int:
    """Parse the first season number from a season field."""

    numbers = extract_episode_numbers(value)
    if not numbers:
        return 1
    return numbers[0]
