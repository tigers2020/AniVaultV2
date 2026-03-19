"""Responsive theme density selection based on window size.

This module is intentionally GUI-library-agnostic: it only maps (width, height)
into a discrete density key and provides scale factors / metric multipliers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DensityKey = Literal["compact", "standard", "expanded", "spacious"]


@dataclass(frozen=True, slots=True)
class DensityProfile:
    """Discrete profile used to generate a QSS variant."""

    key: DensityKey
    scale: float

    # Metric multipliers (mostly scale, but we keep them explicit for future tuning)
    radius_scale: float
    sidebar_width_scale: float
    grid_spacing_scale: float
    card_min_width_scale: float


_PROFILES: dict[DensityKey, DensityProfile] = {
    "compact": DensityProfile(
        key="compact",
        scale=0.92,
        radius_scale=0.92,
        sidebar_width_scale=0.90,
        grid_spacing_scale=0.90,
        card_min_width_scale=0.90,
    ),
    "standard": DensityProfile(
        key="standard",
        scale=1.00,
        radius_scale=1.00,
        sidebar_width_scale=1.00,
        grid_spacing_scale=1.00,
        card_min_width_scale=1.00,
    ),
    "expanded": DensityProfile(
        key="expanded",
        scale=1.08,
        radius_scale=1.06,
        sidebar_width_scale=1.05,
        grid_spacing_scale=1.05,
        card_min_width_scale=1.02,
    ),
    "spacious": DensityProfile(
        key="spacious",
        scale=1.14,
        radius_scale=1.10,
        sidebar_width_scale=1.08,
        grid_spacing_scale=1.08,
        card_min_width_scale=1.04,
    ),
}


def choose_density_key(*, width: int, height: int) -> DensityKey:
    """Pick the density key using both width and height.

    Rules are tuned for AniVault's minimum size (1280x768). The goal is:
    - smaller windows => compact UI (less padding, tighter radius)
    - larger windows => spacious UI (bigger typography and card density)
    """

    # Guard against weird negative/None conversions.
    w = max(0, int(width))
    h = max(0, int(height))

    # Height is a proxy for "vertical real estate" which affects perception
    # of density more than pure width in this app.
    if w < 1260 or h < 740:
        return "compact"

    if w < 1500 or h < 860:
        return "standard"

    if w < 1780 or h < 980:
        return "expanded"

    return "spacious"


def get_profile(key: DensityKey) -> DensityProfile:
    """Get density profile by key."""

    return _PROFILES[key]


def clamp_int(value: float, *, minimum: int, maximum: int) -> int:
    v = int(round(value))
    return max(minimum, min(maximum, v))


def scaled_int(
    base: int, multiplier: float, *, minimum: int | None = None, maximum: int | None = None
) -> int:
    """Scale an integer with optional clamping."""

    v = int(round(base * multiplier))
    if minimum is not None:
        v = max(minimum, v)
    if maximum is not None:
        v = min(maximum, v)
    return v
