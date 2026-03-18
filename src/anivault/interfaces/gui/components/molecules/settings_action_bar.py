"""Settings action bar: Save, Reset, Load buttons (molecule)."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from anivault.interfaces.gui.components.atoms import Button


class SettingsActionBar(QWidget):
    """Save/Reset/Load button row. Emits signals only."""

    save_clicked = Signal()
    reset_clicked = Signal()
    load_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        save_btn = Button("Save", "primary")
        save_btn.clicked.connect(self.save_clicked.emit)
        layout.addWidget(save_btn)
        reset_btn = Button("Reset")
        reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(reset_btn)
        load_btn = Button("Load")
        load_btn.clicked.connect(self.load_clicked.emit)
        layout.addWidget(load_btn)
