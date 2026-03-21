"""operations_presenter.py

Operations 페이지와 apply/rollback 유스케이스 오케스트레이션.

Author: Pom Kim
"""

from PySide6.QtCore import QObject


class OperationsPresenter(QObject):
    """실행 탭 단일 오케스트레이션. Phase 4에서 Worker 연동 예정."""

    def __init__(self, parent: QObject | None = None) -> None:
        """Presenter를 초기화한다.

        Args:
            self: 이 Presenter.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)

    def on_apply_clicked(self) -> None:
        """Move Files / Create Folder Tree 클릭. Phase 4: apply 유스케이스.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        pass

    def on_rollback_clicked(self) -> None:
        """Undo Last Move 클릭. Phase 4: rollback 유스케이스.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        pass
