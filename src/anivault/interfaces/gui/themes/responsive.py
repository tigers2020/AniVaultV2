"""responsive.py

창 크기에 따른 밀도 키·스케일 팩터. Qt에 직접 의존하지 않는다.

Author: Pom Kim
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DensityKey = Literal["compact", "standard", "expanded", "spacious"]


@dataclass(frozen=True, slots=True)
class DensityProfile:
    """이산 밀도 프로필(반경·사이드바·그리드 배율)."""

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
    """너비·높이로 밀도 키를 고른다(최소 1280x768 전후 기준).

    Args:
        width: 창 너비.
        height: 창 높이.

    Returns:
        compact | standard | expanded | spacious.
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
    """키에 해당하는 DensityProfile을 반환한다.

    Args:
        key: 밀도 키.

    Returns:
        프로필 인스턴스.
    """

    return _PROFILES[key]


def clamp_int(value: float, *, minimum: int, maximum: int) -> int:
    """실수를 반올림한 뒤 [minimum, maximum]으로 자른다.

    Args:
        value: 원본 값.
        minimum: 하한.
        maximum: 상한.

    Returns:
        정수.
    """
    v = int(round(value))
    return max(minimum, min(maximum, v))


def scaled_int(
    base: int, multiplier: float, *, minimum: int | None = None, maximum: int | None = None
) -> int:
    """정수 base에 배율을 곱하고 선택적으로 자른다.

    Args:
        base: 기준 픽셀.
        multiplier: 곱할 배율.
        minimum: 선택 하한.
        maximum: 선택 상한.

    Returns:
        스케일된 정수.
    """

    v = int(round(base * multiplier))
    if minimum is not None:
        v = max(minimum, v)
    if maximum is not None:
        v = min(maximum, v)
    return v
