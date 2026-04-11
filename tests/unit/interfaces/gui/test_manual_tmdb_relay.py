from __future__ import annotations

from PySide6.QtCore import QObject

from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.interfaces.gui.presenters.organizing import manual_tmdb_relay as module


class _Dialog:
    def __init__(self) -> None:
        self.candidates_calls: list[list[TmdbSeriesCandidate]] = []
        self.busy_calls: list[bool] = []

    def set_candidates(self, candidates: list[TmdbSeriesCandidate]) -> None:
        self.candidates_calls.append(candidates)

    def set_search_busy(self, busy: bool) -> None:
        self.busy_calls.append(busy)


def _candidate(tmdb_id: int = 7) -> TmdbSeriesCandidate:
    return TmdbSeriesCandidate(
        tmdb_id=tmdb_id,
        name_ko="Frieren",
        original_name="Sousou no Frieren",
        first_air_date="2023-09-29",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="",
        popularity=1.0,
    )


def test_on_result_accepts_candidate_sequences() -> None:
    dlg = _Dialog()
    relay = module.ManualTmdbSearchRelay(dlg, QObject())
    candidates = [_candidate(1), _candidate(2)]

    relay.on_result(candidates)

    assert dlg.candidates_calls == [candidates]


def test_on_result_clears_candidates_for_invalid_payload() -> None:
    dlg = _Dialog()
    relay = module.ManualTmdbSearchRelay(dlg, QObject())

    relay.on_result([_candidate(1), object()])

    assert dlg.candidates_calls == [[]]


def test_on_finished_clears_busy_and_deletes_later(monkeypatch) -> None:
    dlg = _Dialog()
    relay = module.ManualTmdbSearchRelay(dlg, QObject())
    deleted: list[bool] = []
    monkeypatch.setattr(
        module.ManualTmdbSearchRelay, "deleteLater", lambda self: deleted.append(True)
    )

    relay.on_finished()

    assert dlg.busy_calls == [False]
    assert deleted == [True]


def test_on_error_logs_and_shows_generic_translated_message(monkeypatch) -> None:
    dlg = _Dialog()
    relay = module.ManualTmdbSearchRelay(dlg, QObject())
    translations: list[object] = []
    warnings: list[tuple[object, str, str]] = []
    logged: list[tuple[str, Exception]] = []

    def _translate(key: object) -> str:
        translations.append(key)
        return f"translated:{key}"

    def _warning(parent: object, title: str, message: str) -> None:
        warnings.append((parent, title, message))

    def _log(message: str, *, exc_info: Exception) -> None:
        logged.append((message, exc_info))

    monkeypatch.setattr(module, "translate", _translate)
    monkeypatch.setattr(module.QMessageBox, "warning", _warning)
    monkeypatch.setattr(module.logger, "warning", _log)
    err = RuntimeError("sensitive detail")

    relay.on_error(err)

    assert dlg.busy_calls == [False]
    assert len(translations) == 2
    assert logged == [("Manual TMDB search failed", err)]
    assert warnings == [
        (
            dlg,
            f"translated:{module.ORG_MANUAL_TMDB_ERROR_TITLE}",
            f"translated:{module.ORG_MANUAL_TMDB_ERROR_MESSAGE}",
        )
    ]
