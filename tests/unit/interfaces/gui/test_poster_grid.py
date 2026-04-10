from __future__ import annotations

from PySide6.QtWidgets import QApplication

from anivault.interfaces.gui.components.molecules.poster_card import PosterCard
from anivault.interfaces.gui.components.organisms.poster_grid import PosterGrid


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


def _compact_cards(n: int) -> list[PosterCard]:
    return [
        PosterCard(
            title=f"T{i}",
            meta="",
            path="",
            image_url="",
            variant="compact",
            title_only=True,
        )
        for i in range(n)
    ]


def _assert_cards_are_embedded(cards: list[PosterCard]) -> None:
    assert cards
    parents = {c.parent() for c in cards}
    assert len(parents) == 1
    parent = next(iter(parents))
    assert parent is not None
    for card in cards:
        assert card.parent() is parent
        assert not card.isWindow()


def test_poster_grid_set_cards_keeps_cards_embedded() -> None:
    _ensure_app()
    grid = PosterGrid(show_header=False, min_card_width=100)
    grid.resize(480, 360)
    QApplication.processEvents()
    grid.set_cards(_compact_cards(4))
    QApplication.processEvents()
    _assert_cards_are_embedded(grid.cards())


def test_poster_grid_resize_relayout_keeps_cards_embedded() -> None:
    _ensure_app()
    grid = PosterGrid(show_header=False, min_card_width=100)
    grid.resize(400, 360)
    QApplication.processEvents()
    grid.set_cards(_compact_cards(6))
    QApplication.processEvents()
    grid.resize(900, 360)
    QApplication.processEvents()
    _assert_cards_are_embedded(grid.cards())


def test_poster_grid_clear_then_refill_keeps_cards_embedded() -> None:
    _ensure_app()
    grid = PosterGrid(show_header=False, min_card_width=100)
    grid.resize(480, 360)
    QApplication.processEvents()
    grid.set_cards(_compact_cards(3))
    QApplication.processEvents()
    grid.set_cards([])
    QApplication.processEvents()
    grid.set_cards(_compact_cards(2))
    QApplication.processEvents()
    _assert_cards_are_embedded(grid.cards())
