"""Sidebar: Brand + Nav + Pipeline card + Footer."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Pill
from anivault.interfaces.gui.components.molecules import Brand, NavItem, StepRow
from anivault.interfaces.gui.themes import on_density_changed


class Sidebar(QWidget):
    """Left sidebar: brand, main nav, pipeline steps, footer."""

    tab_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._apply_responsive_metrics()
        self.setStyleSheet(theme.sidebar())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 24)
        layout.setSpacing(0)
        layout.addWidget(Brand())
        nav_title = QLabel("Main Views")
        nav_title.setStyleSheet(theme.sidebar_nav_title())
        layout.addWidget(nav_title)
        self._organizer_btn = NavItem("Organizer", "organizer")
        self._organizer_btn.setChecked(True)
        self._operations_btn = NavItem("Operations", "operations")
        self._settings_btn = NavItem("Settings", "settings")
        for btn in (self._organizer_btn, self._operations_btn, self._settings_btn):
            btn.tab_clicked.connect(self.tab_clicked.emit)
            layout.addWidget(btn)
        card = QFrame()
        card.setObjectName("sidebar_pipeline_card")
        card.setStyleSheet(theme.sidebar_card())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(0)
        card_title = QLabel("Pipeline")
        card_title.setStyleSheet(theme.sidebar_card_title())
        card_layout.addWidget(card_title)
        steps = [
            (1, "폴더 스캔", "비디오 파일 수집"),
            (2, "파일명 Parse", "원본 제목, 시즌, 해상도 추출"),
            (3, "Parse Title Group", "정규화된 제목끼리 1차 그룹"),
            (4, "TMDB Scan", "한글 제목, 연도, 시즌 정보 확인"),
            (5, "한글 제목 Group", "최종 그룹명 확정"),
            (6, "구조화 Move", "Resolution → Year → 한글 제목 → Season##"),
        ]
        for idx, title, desc in steps:
            card_layout.addWidget(StepRow(idx, title, desc))
        layout.addWidget(card)
        layout.addStretch()
        footer = QFrame()
        footer.setStyleSheet(theme.sidebar_footer())
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(14, 14, 14, 14)
        footer_layout.addWidget(QLabel("Output Pattern"))
        value = QLabel(r"Target\Resolution\Year\한글 제목\Season##\Original File")
        value.setStyleSheet(theme.sidebar_footer_value())
        value.setWordWrap(True)
        footer_layout.addWidget(value)
        pills = QWidget()
        pills_layout = QVBoxLayout(pills)
        pills_layout.setContentsMargins(0, 8, 0, 0)
        pills_layout.addWidget(Pill("TMDB Linked", "green"))
        pills_layout.addWidget(Pill("Original Filename Kept", "blue"))
        footer_layout.addWidget(pills)
        layout.addWidget(footer)

        on_density_changed(self._apply_responsive_metrics)

    def set_active_tab(self, tab_id: str) -> None:
        self._organizer_btn.setChecked(tab_id == "organizer")
        self._operations_btn.setChecked(tab_id == "operations")
        self._settings_btn.setChecked(tab_id == "settings")

    def _apply_responsive_metrics(self) -> None:
        self.setFixedWidth(theme.sidebar_width_px())
