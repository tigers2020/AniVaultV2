"""__init__.py

테마 레지스트리: 현재 테마·밀도, 저장/로드, 변경 콜백.

Author: Pom Kim
"""

import json
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from anivault.interfaces.gui.themes.dark import DarkTheme
from anivault.interfaces.gui.themes.light import LightTheme
from anivault.interfaces.gui.themes.responsive import DensityKey, choose_density_key, get_profile

_THEMES: dict[str, type] = {
    "dark": DarkTheme,
    "light": LightTheme,
}
_current_theme_name = "dark"
_current: DarkTheme | LightTheme | None = None
_on_color_theme_changed: list[Callable[[], None]] = []
_on_density_changed: list[Callable[[], None]] = []

_current_density_key: DensityKey = "standard"

CONFIG_DIR = Path.home() / ".anivault"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _ensure_current() -> DarkTheme | LightTheme:
    """필요 시 현재 테마 인스턴스를 생성해 반환한다.

    Args:
        없음.

    Returns:
        DarkTheme 또는 LightTheme 인스턴스.
    """
    global _current
    if _current is None:
        profile = get_profile(_current_density_key)
        # scale impacts typography density and metric values (radius, spacing, etc).
        _current = _THEMES[_current_theme_name](scale=profile.scale)
    return _current


def list_themes() -> list[str]:
    """등록된 테마 이름 목록을 반환한다.

    Args:
        없음.

    Returns:
        테마 키 리스트.
    """
    return list(_THEMES.keys())


def get_theme(name: str) -> DarkTheme | LightTheme:
    """이름으로 새 테마 인스턴스를 만든다(현재 밀도 스케일 사용).

    Args:
        name: 테마 키.

    Returns:
        테마 인스턴스.
    """
    cls = _THEMES.get(name) or DarkTheme
    profile = get_profile(_current_density_key)
    return cls(scale=profile.scale)


def get_current_theme() -> DarkTheme | LightTheme:
    """싱글톤에 가까운 현재 테마 인스턴스를 반환한다.

    Args:
        없음.

    Returns:
        현재 테마.
    """
    return _ensure_current()


def set_current_theme(name: str, notify: bool = True) -> None:
    """현재 테마를 바꾸고 선택적으로 리스너를 호출한다.

    Args:
        name: 테마 키. 없으면 무시.
        notify: True이면 on_theme_changed 콜백 실행.

    Returns:
        None.
    """
    global _current, _current_theme_name
    if name not in _THEMES:
        return
    _current_theme_name = name
    profile = get_profile(_current_density_key)
    _current = _THEMES[name](scale=profile.scale)
    if notify:
        for cb in _on_color_theme_changed:
            cb()


def get_current_density_key() -> DensityKey:
    """현재 반응형 밀도 키를 반환한다.

    Args:
        없음.

    Returns:
        DensityKey.
    """
    return _current_density_key


def set_responsive_density_key(key: DensityKey, notify: bool = True) -> None:
    """밀도 키를 갱신하고 테마 인스턴스를 무효화한다.

    Args:
        key: 새 밀도 키.
        notify: True이면 on_density_changed 콜백 실행.

    Returns:
        None.
    """
    global _current_density_key, _current
    if key == _current_density_key:
        return

    _current_density_key = key
    # Force re-creation so theme instances can embed density-specific QSS metrics.
    _current = None
    if notify:
        for cb in _on_density_changed:
            cb()


def set_responsive_density_for_size(*, width: int, height: int, notify: bool = True) -> DensityKey:
    """창 크기로 밀도를 계산·적용한다.

    Args:
        width: 창 너비.
        height: 창 높이.
        notify: 콜백 호출 여부.

    Returns:
        적용된 DensityKey.
    """
    key = choose_density_key(width=width, height=height)
    set_responsive_density_key(key, notify=notify)
    return key


def get_current_theme_name() -> str:
    """현재 테마 이름 문자열을 반환한다.

    Args:
        없음.

    Returns:
        dark | light 등.
    """
    return _current_theme_name


def on_theme_changed(callback: Callable[[], None]) -> None:
    """라이트/다크 전환 시 호출할 콜백을 등록한다.

    Args:
        callback: 인자 없는 호출 가능 객체.

    Returns:
        None.
    """
    _on_color_theme_changed.append(callback)


def on_density_changed(callback: Callable[[], None]) -> None:
    """밀도 키 변경 시 호출할 콜백을 등록한다.

    Args:
        callback: 인자 없는 호출 가능 객체.

    Returns:
        None.
    """
    _on_density_changed.append(callback)


def load_saved_theme() -> None:
    """설정 파일에서 테마를 읽어 적용한다(시작 시). 리스너는 호출하지 않는다.

    Args:
        없음.

    Returns:
        None.
    """
    if not CONFIG_FILE.exists():
        return
    with suppress(OSError, ValueError, KeyError):
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        name = data.get("theme")
        if name and name in _THEMES:
            set_current_theme(name, notify=False)


def save_theme(name: str) -> None:
    """테마 이름을 설정 파일에 저장한다.

    Args:
        name: 저장할 테마 키.

    Returns:
        None.
    """
    with suppress(OSError):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data: dict[str, str] = {}
        if CONFIG_FILE.exists():
            with suppress(OSError, ValueError):
                loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
        data["theme"] = name
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
