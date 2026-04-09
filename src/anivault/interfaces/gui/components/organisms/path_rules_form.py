"""path_rules_form.py

정리 대상 루트와 경로 템플릿 설정 폼.

Author: Pom Kim
"""

import re

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.constants.gui.components import (
    PATH_RULES_FORM_HEADER_DESCRIPTION,
    PATH_RULES_FORM_HEADER_TITLE,
    PATH_RULES_FORM_LABEL_TARGET_ROOT,
    PATH_RULES_FORM_LABEL_TEMPLATE,
    PATH_RULES_FORM_LABEL_UNKNOWN_GROUP,
    PATH_RULES_FORM_LABEL_UNKNOWN_RESOLUTION,
)
from anivault.constants.gui.forms import PATH_TEMPLATE_EXAMPLES
from anivault.constants.gui.settings import DEFAULT_PATH_RULES
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import FormField, PanelHeader


def _template_to_example(template: str) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        base = key.split(":")[0]
        return PATH_TEMPLATE_EXAMPLES.get(base, f"{{{key}}}")

    return re.sub(r"\{([^}]+)\}", repl, template)


def _path_template_label(template: str) -> str:
    example = _template_to_example(template)
    return f"{PATH_RULES_FORM_LABEL_TEMPLATE} ({example})"


class PathRulesForm(QFrame):
    """경로 규칙 입력 폼."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(PATH_RULES_FORM_HEADER_TITLE, PATH_RULES_FORM_HEADER_DESCRIPTION)
        )
        body = QVBoxLayout()
        body_padding = theme.settings_card_body_padding_px()
        body.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        body.setSpacing(theme.settings_section_gap_px())
        self._target_root = FormField(
            PATH_RULES_FORM_LABEL_TARGET_ROOT,
            "path",
            str(DEFAULT_PATH_RULES["target_root"]),
        )
        self._path_template = FormField(
            PATH_RULES_FORM_LABEL_TEMPLATE,
            "line",
            str(DEFAULT_PATH_RULES["path_template"]),
            label_updater=_path_template_label,
        )
        self._unknown_resolution = FormField(
            PATH_RULES_FORM_LABEL_UNKNOWN_RESOLUTION,
            "line",
            str(DEFAULT_PATH_RULES["unknown_resolution"]),
        )
        self._unknown_group = FormField(
            PATH_RULES_FORM_LABEL_UNKNOWN_GROUP,
            "line",
            str(DEFAULT_PATH_RULES["unknown_group_folder"]),
        )
        for field in (
            self._target_root,
            self._path_template,
            self._unknown_resolution,
            self._unknown_group,
        ):
            body.addWidget(field)
            field.value_changed.connect(self.settings_changed.emit)
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
