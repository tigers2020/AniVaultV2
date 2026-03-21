"""path_rules_form.py

정리 대상 루트·경로 템플릿·미지정 해상도/그룹 폴더명 설정 폼.

Author: Pom Kim
"""

import re

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import FormField, PanelHeader

_PATH_TEMPLATE_EXAMPLES = {
    "target": "G:/AniSorted",
    "resolution": "1080p",
    "year": "2024",
    "korean_title_group": "애니제목",
    "season": "01",
    "original_filename": "원본파일명.mkv",
}


def _template_to_example(template: str) -> str:
    """경로 템플릿의 `{키}` 자리를 예시 문자열로 치환한 미리보기를 만든다.

    Args:
        template: 원본 템플릿 문자열.

    Returns:
        치환된 예시 경로 문자열.
    """

    def repl(m: re.Match[str]) -> str:
        """단일 `{...}` 매치를 예시 값 또는 원문 플레이스홀더로 바꾼다.

        Args:
            m: 정규식 매치.

        Returns:
            치환 문자열.
        """
        key = m.group(1)
        base = key.split(":")[0]
        return _PATH_TEMPLATE_EXAMPLES.get(base, f"{{{key}}}")

    return re.sub(r"\{([^}]+)\}", repl, template)


def _path_template_label(template: str) -> str:
    """FormField 라벨에 붙일 'Path template (예시)' 문자열을 만든다.

    Args:
        template: 경로 템플릿.

    Returns:
        라벨 텍스트.
    """
    example = _template_to_example(template)
    return f"Path template ({example})"


class PathRulesForm(QFrame):
    """경로 규칙 입력 필드와 settings_changed 시그널."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        """폼 필드·시그널 연결을 구성한다.

        Args:
            self: 이 폼 인스턴스.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(PanelHeader("Path Rules", "최종 출력 구조와 기본값 설정"))
        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        self._target_root = FormField("Target root folder", "path", "G:/AniSorted")
        self._path_template = FormField(
            "Path template",
            "line",
            r"{target}\{resolution}\{year}\{korean_title_group}\Season{season:02}\{original_filename}",
            label_updater=_path_template_label,
        )
        self._unknown_resolution = FormField("Unknown resolution", "line", "Unknown")
        self._unknown_group = FormField("Unknown group folder", "line", "Needs_Review")
        for f in (
            self._target_root,
            self._path_template,
            self._unknown_resolution,
            self._unknown_group,
        ):
            body.addWidget(f)
            f.value_changed.connect(self.settings_changed.emit)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def get_values(self) -> dict[str, str]:
        """현재 경로 규칙 값을 딕셔너리로 반환한다.

        Args:
            self: 이 폼 인스턴스.

        Returns:
            설정 키-값 맵.
        """
        return {
            "target_root": self._target_root.value(),
            "path_template": self._path_template.value(),
            "unknown_resolution": self._unknown_resolution.value(),
            "unknown_group_folder": self._unknown_group.value(),
        }

    def set_values(self, data: dict[str, str]) -> None:
        """저장된 맵으로 필드를 채운다(시그널 일시 차단).

        Args:
            self: 이 폼 인스턴스.
            data: 적용할 설정 맵.

        Returns:
            None.
        """
        self.blockSignals(True)
        try:
            if "target_root" in data:
                self._target_root.set_value(data["target_root"])
            if "path_template" in data:
                self._path_template.set_value(data["path_template"])
            if "unknown_resolution" in data:
                self._unknown_resolution.set_value(data["unknown_resolution"])
            if "unknown_group_folder" in data:
                self._unknown_group.set_value(data["unknown_group_folder"])
        finally:
            self.blockSignals(False)
