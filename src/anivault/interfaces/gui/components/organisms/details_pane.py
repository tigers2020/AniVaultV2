"""Details pane: right-side panel showing selected row fields."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineRow


def _member_lines(group: PipelineGroupRow) -> str:
    parts: list[str] = []
    for m in group.members:
        name = Path(m.original_file).name
        extra = " · ".join(p for p in (m.season or "", m.resolution or "") if (p or "").strip())
        if extra:
            parts.append(f"{name}<br><small>{extra}</small>")
        else:
            parts.append(name)
    return "<br>".join(parts)


class DetailsPane(QFrame):
    """Right pane: fields of selected file or group of files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)
        self.setMaximumWidth(480)
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

    def set_row(self, row: PipelineRow | PipelineGroupRow | None) -> None:
        if row is None:
            self._content.setText("항목을 선택하세요")
            return
        if isinstance(row, PipelineGroupRow):
            if len(row.members) > 1:
                files_block = _member_lines(row)
                self._content.setText(
                    f"<b>파일 ({len(row.members)}개)</b><br>{files_block}<br><br>"
                    f"<b>Parsed Title</b><br>{row.parsed_title}<br><br>"
                    f"<b>Parse Group</b><br>{row.parse_group}<br><br>"
                    f"<b>TMDB 한글</b><br>{row.tmdb_korean_title_group}<br><br>"
                    f"<b>Year / Season</b><br>{row.year} / {row.season}<br><br>"
                    f"<b>해상도</b><br>{row.resolution}<br><br>"
                    f"<b>상태</b><br>{row.status}<br><br>"
                    f"<b>대상 경로</b><br>{row.target_path}"
                )
            else:
                only = row.members[0]
                self._set_single_row(only)
            return
        self._set_single_row(row)

    def _set_single_row(self, row: PipelineRow) -> None:
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
