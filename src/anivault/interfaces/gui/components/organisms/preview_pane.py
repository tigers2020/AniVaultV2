"""preview_pane.py

선택된 파이프라인 행의 포스터 영역을 보여 주는 우측 미리보기 패널.

Author: Pom Kim
"""

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import RoundedPixmapLabel
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineRow


class PreviewPane(QFrame):
    """선택 행의 큰 포스터(또는 플레이스홀더)를 표시하는 우측 패널."""

    def __init__(self, parent=None):
        """이미지 라벨·레이아웃·스타일을 초기화한다.

        Args:
            self: 이 패널 인스턴스.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        self._img = RoundedPixmapLabel()
        self._img.setMinimumHeight(360)
        self._img.set_placeholder_text("항목을 선택하세요")
        layout.addWidget(self._img)

        self.setStyleSheet(theme.card_panel())

    def set_row(self, row: PipelineRow | PipelineGroupRow | None) -> None:
        """선택 행에 맞춰 플레이스홀더 텍스트를 갱신한다(비동기 포스터는 별도).

        Args:
            self: 이 패널 인스턴스.
            row: 단일 행 또는 그룹. None이면 빈 상태.

        Returns:
            None.
        """
        if row is None:
            self._img.clear_source_pixmap()
            self._img.set_placeholder_text("항목을 선택하세요")
            return
        rep = row
        if isinstance(row, PipelineGroupRow):
            rep = row.representative()
            for m in row.members:
                if (m.tmdb_korean_title_group or "").strip():
                    rep = m
                    break
        # Poster loading is async elsewhere; for now show placeholder
        self._img.clear_source_pixmap()
        self._img.set_placeholder_text(f"Poster\n{rep.tmdb_korean_title_group}")

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """미리보기 영역에 픽스맵을 직접 설정하거나 비운다.

        Args:
            self: 이 패널 인스턴스.
            pixmap: 표시할 픽스맵. None이면 클리어.

        Returns:
            None.
        """
        if pixmap is not None and not pixmap.isNull():
            self._img.set_source_pixmap(pixmap)
        else:
            self._img.clear_source_pixmap()
            self._img.set_placeholder_text("Poster")
