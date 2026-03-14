"""Button with variants: default, primary, success, warn, danger."""

from PySide6.QtWidgets import QPushButton


class Button(QPushButton):
    """Styled button. Set objectName to 'primary', 'success', 'warn', 'danger' for variants."""

    def __init__(self, text: str = "", variant: str = "default", parent=None):
        super().__init__(text, parent)
        if variant != "default":
            self.setObjectName(variant)
