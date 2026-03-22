"""progress_dialog.py

장시간 작업용 모달 진행 대화상자.

Author: Pom Kim
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QProgressDialog, QWidget

from anivault.interfaces.gui import theme


class ProgressDialog(QProgressDialog):
    """스캔·TMDB·빌드 등에 쓰는 테마 스타일 진행 창."""

    finished = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """모달·최소 표시 시간·취소 시그널을 설정한다.

        Args:
            self: 이 대화상자.
            parent: 부모 위젯.

        Returns:
            None.
        """
        super().__init__(parent)
        self.setStyleSheet(theme.progress_dialog())
        self.setMinimumDuration(0)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle("진행 중")
        self.canceled.connect(self._on_canceled)
        self.setAutoClose(False)
        self.setAutoReset(False)
        self._progress_session_id: int = 0

    @property
    def progress_session_id(self) -> int:
        """Presenter에서 progress 토큰과 비교할 때 쓰는 세션 ID.

        Args:
            self: 이 대화상자.

        Returns:
            세션 정수.
        """
        return self._progress_session_id

    def mark_work_started(self) -> int:
        """현재 진행 세션 ID를 반환한다. 워커 시작 직후 progress 연결에 캡처한다.

        Args:
            self: 이 대화상자.

        Returns:
            이번 작업에 매칭할 세션 정수.
        """
        return self._progress_session_id

    def mark_work_finished(self) -> None:
        """작업 종료 시 호출해 세션을 올린다. 큐에 남은 stale progress를 무효화한다.

        Args:
            self: 이 대화상자.

        Returns:
            None.
        """
        self._progress_session_id += 1

    def is_progress_token_valid(self, token: int) -> bool:
        """Progress 슬롯이 아직 유효한 세션인지 본다.

        Args:
            self: 이 대화상자.
            token: mark_work_started에서 캡처한 값.

        Returns:
            유효하면 True.
        """
        return token == self._progress_session_id

    def _on_canceled(self) -> None:
        """취소 시 finished를보낸다.

        Args:
            self: 이 대화상자.

        Returns:
            None.
        """
        self.finished.emit()

    def show_progress(
        self,
        title: str = "진행 중",
        message: str = "",
        indeterminate: bool = True,
    ) -> None:
        """즉시 표시한다. indeterminate면 범위 0,0(버지).

        Args:
            self: 이 대화상자.
            title: 창 제목.
            message: 라벨 메시지.
            indeterminate: True면 무한 진행 막대.

        Returns:
            None.
        """
        self.setWindowTitle(title)
        self.setLabelText(message or "처리 중입니다...")
        self.setRange(0, 0 if indeterminate else 100)
        if indeterminate:
            self.setValue(0)
        else:
            self.setValue(0)
            self.setMaximum(100)
        self.show()
        self.raise_()
        self.activateWindow()

    def update_progress(
        self,
        message: str | None = None,
        value: int | None = None,
        maximum: int = 100,
    ) -> None:
        """메시지와/또는 진행 값을 갱신한다(QWidget.update와 이름 충돌 방지).

        Args:
            self: 이 대화상자.
            message: 새 라벨 텍스트. None이면 유지.
            value: 진행 값. None이면 유지.
            maximum: 확정 모드일 때 최댓값.

        Returns:
            None.
        """
        if message is not None:
            self.setLabelText(message)
        if value is not None:
            self.setMaximum(maximum)
            self.setValue(value)

    def hide_progress(self) -> None:
        """완료·오류·취소 후 리셋하고 숨긴다.

        Args:
            self: 이 대화상자.

        Returns:
            None.
        """
        self.reset()
        self.hide()
