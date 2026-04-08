"""OrganizerPage 통계 카드가 modelReset 외 증분 모델 시그널에서도 갱신되는지 검증한다."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from anivault.interfaces.gui.components.organisms.stats_grid import StatsGrid
from anivault.interfaces.gui.models import PipelineRow, group_pipeline_rows
from anivault.interfaces.gui.pages import organizer_page as organizer_page_module
from anivault.interfaces.gui.pages.organizer_page import OrganizerPage


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


def test_update_stats_on_append_row_groups_after_model_reset(monkeypatch) -> None:
    """청크 적용 시 append_row_groups(rowsInserted)만 발생해도 통계가 갱신된다."""
    _ensure_app()
    stats_calls: list[dict[str, int]] = []

    def tracking_set_stats(
        self,
        *,
        scanned: int = 0,
        parsed: int = 0,
        tmdb_matches: int = 0,
        groups: int = 0,
    ) -> None:
        stats_calls.append(
            {
                "scanned": scanned,
                "parsed": parsed,
                "tmdb_matches": tmdb_matches,
                "groups": groups,
            }
        )

    monkeypatch.setattr(StatsGrid, "set_stats", tracking_set_stats)
    monkeypatch.setattr(
        organizer_page_module,
        "load_all",
        lambda: {"scan_build": {"source_path": ""}},
    )

    page = OrganizerPage()
    assert stats_calls[-1] == {
        "scanned": 0,
        "parsed": 0,
        "tmdb_matches": 0,
        "groups": 0,
    }

    row = PipelineRow(
        original_file="/x/a.mkv",
        parsed_title="Show",
        parse_group="g",
        tmdb_korean_title_group="한글",
        tmdb_series_id="",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="",
        season="",
        resolution="",
        status="parsed",
        poster_url="",
        backdrop_url="",
        target_path="",
    )
    page._model.append_row_groups(group_pipeline_rows([row]))

    assert stats_calls[-1] == {
        "scanned": 1,
        "parsed": 1,
        "tmdb_matches": 1,
        "groups": 1,
    }
