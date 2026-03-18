"""Progress dialog: reusable modal for long-running operations."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QProgressDialog, QWidget

from anivault.interfaces.gui import theme


class ProgressDialog(QProgressDialog):
    """Theme-styled progress dialog for scan, TMDB query, build, etc."""

    finished = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(theme.progress_dialog())
        self.setMinimumDuration(0)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle("진행 중")
        self.canceled.connect(self._on_canceled)

    def _on_canceled(self) -> None:
        self.finished.emit()

    def show_progress(
        self,
        title: str = "진행 중",
        message: str = "",
        indeterminate: bool = True,
    ) -> None:
        """Show dialog immediately. indeterminate=True uses busy bar."""
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
        """Update message and/or progress value. Named to avoid conflict with QWidget.update."""
        if message is not None:
            self.setLabelText(message)
        if value is not None:
            self.setMaximum(maximum)
            self.setValue(value)
