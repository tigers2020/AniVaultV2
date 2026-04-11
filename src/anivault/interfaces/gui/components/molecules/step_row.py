"""step_row.py

StepIndex + 제목·설명 텍스트 한 줄.

Author: Pom Kim
"""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import StepIndex


def _apply_text_color(label: QLabel) -> None:
    """다크 테마에서 HTML/리치텍스트 이슈를 피하도록 팔레트 텍스트 색을 맞춘다.

    Args:
        label: 색을 적용할 QLabel.

    Returns:
        None.
    """
    palette = label.palette()
    palette.setColor(palette.ColorRole.WindowText, QColor(theme.COLORS["text"]))
    label.setPalette(palette)


class StepRow(QWidget):
    """파이프라인 단계: 번호 원 + 텍스트 블록."""

    def __init__(self, index: int, title: str, description: str = "", parent=None):
        """단계 번호와 설명을 배치한다.

        Args:
            self: 이 위젯.
            index: StepIndex에 표시할 번호.
            title: 단계 제목.
            description: 부가 설명(선택).
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        row_gap = theme.layout_spacing_sm_px()
        layout.setSpacing(row_gap)
        layout.setContentsMargins(0, row_gap, 0, row_gap)
        layout.addWidget(StepIndex(index, 24))
        text_wrapper = QWidget()
        text_layout = QVBoxLayout(text_wrapper)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(theme.panel_header_stack_gap_px())
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(theme.step_row_title())
        title_lbl.setWordWrap(True)
        _apply_text_color(title_lbl)
        text_layout.addWidget(title_lbl)
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet(theme.step_row_text())
            desc_lbl.setWordWrap(True)
            _apply_text_color(desc_lbl)
            text_layout.addWidget(desc_lbl)
        layout.addWidget(text_wrapper, 1)
