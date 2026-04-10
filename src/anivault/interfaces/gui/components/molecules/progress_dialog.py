"""Modal progress dialog used across organizer workflows."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QProgressDialog, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.i18n import translate
from anivault.interfaces.gui.i18n.keys import PROGRESS_DEFAULT_MESSAGE, PROGRESS_DEFAULT_TITLE


class ProgressDialog(QProgressDialog):
    """Theme-styled progress dialog for long-running UI tasks."""

    finished = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(theme.progress_dialog())
        self.setMinimumDuration(0)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle(translate(PROGRESS_DEFAULT_TITLE))
        self.canceled.connect(self._on_canceled)
        self.setAutoClose(False)
        self.setAutoReset(False)
        self._progress_session_id: int = 0

    @property
    def progress_session_id(self) -> int:
        return self._progress_session_id

    def mark_work_started(self) -> int:
        return self._progress_session_id

    def mark_work_finished(self) -> None:
        self._progress_session_id += 1

    def is_progress_token_valid(self, token: int) -> bool:
        return token == self._progress_session_id

    def _on_canceled(self) -> None:
        self.finished.emit()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(translate(PROGRESS_DEFAULT_TITLE))
        if not self.isVisible():
            self.setLabelText(translate(PROGRESS_DEFAULT_MESSAGE))

    def show_progress(
        self,
        title: str | None = None,
        message: str = "",
        indeterminate: bool = True,
    ) -> None:
        resolved_title = translate(PROGRESS_DEFAULT_TITLE) if title is None else title
        self.setWindowTitle(resolved_title)
        self.setLabelText(message or translate(PROGRESS_DEFAULT_MESSAGE))
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
        if message is not None:
            self.setLabelText(message)
        if value is not None:
            self.setMaximum(maximum)
            self.setValue(value)

    def hide_progress(self) -> None:
        self.reset()
        self.hide()
