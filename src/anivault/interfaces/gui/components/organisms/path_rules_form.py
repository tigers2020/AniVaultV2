"""Path rules form: target root, path template, unknown resolution/group."""

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
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        base = key.split(":")[0]
        return _PATH_TEMPLATE_EXAMPLES.get(base, f"{{{key}}}")

    return re.sub(r"\{([^}]+)\}", repl, template)


def _path_template_label(template: str) -> str:
    example = _template_to_example(template)
    return f"Path template ({example})"


class PathRulesForm(QFrame):
    """Path rules panel fields."""

    settings_changed = Signal()

    def __init__(self, parent=None):
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
        return {
            "target_root": self._target_root.value(),
            "path_template": self._path_template.value(),
            "unknown_resolution": self._unknown_resolution.value(),
            "unknown_group_folder": self._unknown_group.value(),
        }

    def set_values(self, data: dict[str, str]) -> None:
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
