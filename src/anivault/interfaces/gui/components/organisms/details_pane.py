"""Details pane: right-side panel showing selected row fields."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.models import PipelineRow


class DetailsPane(QFrame):
    """Right pane: all fields of selected PipelineRow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QLabel()
        self._content.setWordWrap(True)
        self._content.setText("항목을 선택하세요")
        self._content.setStyleSheet(theme.panel_header_desc())
        scroll.setWidget(self._content)
        layout.addWidget(scroll)

        self.setStyleSheet(theme.card_panel())

    def set_row(self, row: PipelineRow | None) -> None:
        if row is None:
            self._content.setText("항목을 선택하세요")
            return
        self._content.setText(
            f"<b>원본 파일</b><br>{row.original_file}<br><br>"
            f"<b>Parsed Title</b><br>{row.parsed_title}<br><br>"
            f"<b>Parse Group</b><br>{row.parse_group}<br><br>"
            f"<b>TMDB 한글</b><br>{row.tmdb_korean_title_group}<br><br>"
            f"<b>Year / Season</b><br>{row.year} / {row.season}<br><br>"
            f"<b>해상도</b><br>{row.resolution}<br><br>"
            f"<b>상태</b><br>{row.status}<br><br>"
            f"<b>대상 경로</b><br>{row.target_path}"
        )
