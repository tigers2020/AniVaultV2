"""Stats grid: 4 StatCards (Scanned Files, Parsed Titles, TMDB Matches, Planned Moves)."""

from PySide6.QtWidgets import QGridLayout, QWidget

from anivault.interfaces.gui.components.molecules import StatCard


class StatsGrid(QWidget):
    """Four stat cards in a row."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(0, 0, 0, 18)
        self._cards = [
            StatCard("Scanned Files", "9,048"),
            StatCard("Parsed Titles", "8,991"),
            StatCard("TMDB Korean Matches", "8,918"),
            StatCard("Planned Moves", "8,975"),
        ]
        for i, card in enumerate(self._cards):
            layout.addWidget(card, 0, i)
