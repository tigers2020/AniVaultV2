"""View/pane toggle button atom (checkable QToolButton)."""

from PySide6.QtWidgets import QToolButton

from anivault.interfaces.gui import theme


class ViewToggleButton(QToolButton):
    """Small checkable button used for view/pane toggles."""

    def __init__(
        self,
        text: str,
        checked: bool = False,
        object_name: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setChecked(checked)
        if object_name:
            self.setObjectName(object_name)
        self.setStyleSheet(theme.view_toggle_button())
