"""OperationsPresenter: orchestrates OperationsPage <-> apply/rollback use cases."""

from PySide6.QtCore import QObject


class OperationsPresenter(QObject):
    """Single orchestration for Operations page. Apply/rollback via workers."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def on_apply_clicked(self) -> None:
        """Handle Move Files / Create Folder Tree. Phase 4: apply use case."""
        pass

    def on_rollback_clicked(self) -> None:
        """Handle Undo Last Move. Phase 4: rollback use case."""
        pass
