"""path_rules_form.py

정리 대상 루트와 경로 템플릿 설정 폼.

Author: Pom Kim
"""

import re

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.constants.gui.settings import DEFAULT_PATH_RULES
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import FormField, PanelHeader
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K


def _path_template_examples() -> dict[str, str]:
    return {
        "target": translate(K.PATH_TMPL_EX_TARGET),
        "resolution": translate(K.PATH_TMPL_EX_RESOLUTION),
        "year": translate(K.PATH_TMPL_EX_YEAR),
        "korean_title_group": translate(K.PATH_TMPL_EX_KOREAN_GROUP),
        "season": translate(K.PATH_TMPL_EX_SEASON),
        "original_filename": translate(K.PATH_TMPL_EX_FILENAME),
    }


class PathRulesForm(QFrame):
    """경로 규칙 입력 폼."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._header = PanelHeader(
            translate(K.SETTINGS_PATH_RULES_TITLE),
            translate(K.SETTINGS_PATH_RULES_DESC),
        )
        layout.addWidget(self._header)
        body = QVBoxLayout()
        body_padding = theme.settings_card_body_padding_px()
        body.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        body.setSpacing(theme.settings_section_gap_px())
        self._target_root = FormField(
            translate(K.SETTINGS_PATH_LABEL_TARGET),
            "path",
            str(DEFAULT_PATH_RULES["target_root"]),
        )
        self._path_template = FormField(
            translate(K.SETTINGS_PATH_LABEL_TEMPLATE),
            "line",
            str(DEFAULT_PATH_RULES["path_template"]),
            label_updater=self._path_template_label,
        )
        self._unknown_resolution = FormField(
            translate(K.SETTINGS_PATH_LABEL_UNKNOWN_RES),
            "line",
            str(DEFAULT_PATH_RULES["unknown_resolution"]),
        )
        self._unknown_group = FormField(
            translate(K.SETTINGS_PATH_LABEL_UNKNOWN_GRP),
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
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def _path_template_label(self, template: str) -> str:
        examples = _path_template_examples()

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            base = key.split(":")[0]
            return examples.get(base, f"{{{key}}}")

        example = re.sub(r"\{([^}]+)\}", repl, template)
        return f"{translate(K.SETTINGS_PATH_LABEL_TEMPLATE)} ({example})"

    def retranslate_ui(self) -> None:
        self._header.set_header_texts(
            translate(K.SETTINGS_PATH_RULES_TITLE),
            translate(K.SETTINGS_PATH_RULES_DESC),
        )
        self._target_root.apply_static_label(translate(K.SETTINGS_PATH_LABEL_TARGET))
        self._target_root.retranslate_path_placeholder()
        self._unknown_resolution.apply_static_label(translate(K.SETTINGS_PATH_LABEL_UNKNOWN_RES))
        self._unknown_group.apply_static_label(translate(K.SETTINGS_PATH_LABEL_UNKNOWN_GRP))
        self._path_template.apply_static_label(translate(K.SETTINGS_PATH_LABEL_TEMPLATE))
        self._path_template.set_label_updater(self._path_template_label)

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
