"""Stats grid: 4 StatCards (Scanned Files, Parsed Titles, TMDB Matches, Planned Moves)."""

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget

from anivault.interfaces.gui.components.molecules import StatCard


def _fmt(n: int) -> str:
    """Format integer with thousands separator."""
    return f"{n:,}"


class StatsGrid(QWidget):
    """Four stat cards in a row. Update via set_stats()."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(0, 0, 0, 18)
        self._cards = [
            StatCard("Scanned Files", _fmt(0)),
            StatCard("Parsed Titles", _fmt(0)),
            StatCard("TMDB Korean Matches", _fmt(0)),
            StatCard("Planned Moves", _fmt(0)),
        ]
        for i, card in enumerate(self._cards):
            layout.addWidget(card, 0, i)

        # Prevent vertical stretching when embedded in a resizable scroll area.
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed))
        self._sync_fixed_height()

    def set_stats(
        self,
        scanned: int = 0,
        parsed: int = 0,
        tmdb_matches: int = 0,
        planned: int = 0,
    ) -> None:
        """Update card values from pipeline counts."""
        self._cards[0].set_value(_fmt(scanned))
        self._cards[1].set_value(_fmt(parsed))
        self._cards[2].set_value(_fmt(tmdb_matches))
        self._cards[3].set_value(_fmt(planned))

    def _sync_fixed_height(self) -> None:
        """Keep row height aligned to style/font changes."""
        h = int(self.layout().sizeHint().height()) if self.layout() is not None else 0
        if h <= 0:
            h = int(self.sizeHint().height())
        if h > 0:
            self.setFixedHeight(h)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in {
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
            QEvent.Type.Polish,
            QEvent.Type.LayoutRequest,
        }:
            self._sync_fixed_height()
