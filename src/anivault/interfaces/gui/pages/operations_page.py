"""operations_page.py

폴더 구조 미리보기·실행 카드·로그 두 열 페이지.

Author: Pom Kim
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Pill
from anivault.interfaces.gui.components.molecules import StepRow
from anivault.interfaces.gui.components.organisms import (
    ExecutionCard,
    FolderStructurePreview,
    LogList,
)
from anivault.interfaces.gui.presenters import OperationsPresenter


class OperationsPage(QWidget):
    """구조 목록 + 실행 + 로그."""

    def __init__(self, parent=None, presenter: OperationsPresenter | None = None):
        """Presenter를 연결하고 레이아웃을 구성한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).
            presenter: 외부 주입 Presenter. None이면 자체 생성.

        Returns:
            None.
        """
        super().__init__(parent)
        self._presenter = presenter if presenter is not None else OperationsPresenter(parent=self)
        if presenter is not None:
            self._presenter.setParent(self)
        exec_card = ExecutionCard()
        exec_card.apply_clicked.connect(self._presenter.on_apply_clicked)
        exec_card.rollback_clicked.connect(self._presenter.on_rollback_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        content_layout.addWidget(FolderStructurePreview())
        context_row = QWidget()
        context_row_layout = QHBoxLayout(context_row)
        context_row_layout.setContentsMargins(0, 0, 0, 0)
        context_row_layout.setSpacing(16)
        context_row_layout.addWidget(self._build_pipeline_context_card(), 3)
        context_row_layout.addWidget(self._build_output_pattern_card(), 2)
        content_layout.addWidget(context_row)
        two_col = QWidget()
        two_col_layout = QHBoxLayout(two_col)
        two_col_layout.setContentsMargins(0, 0, 0, 0)
        two_col_layout.setSpacing(18)
        two_col_layout.addWidget(exec_card, 12)
        two_col_layout.addWidget(LogList(), 8)
        content_layout.addWidget(two_col)
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _build_pipeline_context_card(self) -> QFrame:
        """파이프라인 단계 StepRow 카드를 만든다.

        Args:
            self: 이 위젯.

        Returns:
            QFrame 카드.
        """
        card = QFrame()
        card.setStyleSheet(theme.sidebar_card())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(6)
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
        return card

    def _build_output_pattern_card(self) -> QFrame:
        """출력 패턴·Pill 안내 카드를 만든다.

        Args:
            self: 이 위젯.

        Returns:
            QFrame 카드.
        """
        card = QFrame()
        card.setStyleSheet(theme.sidebar_footer())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(6)
        title = QLabel("Output Pattern")
        title.setStyleSheet(theme.sidebar_card_title())
        card_layout.addWidget(title)
        value = QLabel(r"Target\Resolution\Year\한글 제목\Season##\Original File")
        value.setStyleSheet(theme.sidebar_footer_value())
        value.setWordWrap(True)
        card_layout.addWidget(value)
        pills = QWidget()
        pills_layout = QVBoxLayout(pills)
        pills_layout.setContentsMargins(0, 8, 0, 0)
        pills_layout.addWidget(Pill("TMDB Linked", "green"))
        pills_layout.addWidget(Pill("Original Filename Kept", "blue"))
        card_layout.addWidget(pills)
        return card
