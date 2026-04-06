"""test_pipeline_table_model_incremental_update.py

PipelineTableModel의 구조 호환 부분 갱신(dataChanged) 경로 테스트.

Author: Pom Kim
"""

from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtCore import QObject

from anivault.interfaces.gui.models import PipelineRow, PipelineTableModel, group_pipeline_rows


class _Spy(QObject):
    """시그널 호출 횟수를 저장하는 스파이 QObject."""

    def __init__(self) -> None:
        """0으로 시작한다.

        Args:
            self: 이 스파이.

        Returns:
            None.
        """
        super().__init__()
        self.calls = 0

    def on_called(self, *_args: object) -> None:
        """연결된 시그널이 emit되면 호출 횟수를 올린다.

        Args:
            *_args: 시그널 인자(미사용).

        Returns:
            None.
        """
        self.calls += 1


def test_update_rows_if_compatible_emits_data_changed_without_model_reset() -> None:
    """구조 호환 시 modelReset 없이 dataChanged만 발생하는지 검증한다.

    Args:
        없음.

    Returns:
        None.
    """
    model = PipelineTableModel()
    model.modelReset = MagicMock()  # type: ignore[method-assign]
    spy = _Spy()
    model.dataChanged.connect(spy.on_called)

    base = [
        PipelineRow(
            original_file="/a/1.mkv",
            parsed_title="A",
            parse_group="A",
            tmdb_korean_title_group="",
            tmdb_series_id="",
            tmdb_poster_path="",
            tmdb_backdrop_path="",
            year="",
            season="",
            resolution="1080p",
            status="스캔됨",
            poster_url="",
            backdrop_url="",
            target_path="",
        ),
        PipelineRow(
            original_file="/a/2.mkv",
            parsed_title="A",
            parse_group="A",
            tmdb_korean_title_group="",
            tmdb_series_id="",
            tmdb_poster_path="",
            tmdb_backdrop_path="",
            year="",
            season="",
            resolution="1080p",
            status="스캔됨",
            poster_url="",
            backdrop_url="",
            target_path="",
        ),
    ]
    model.set_rows(group_pipeline_rows(base))
    model.modelReset.reset_mock()
    spy.calls = 0

    updated = [
        PipelineRow(
            original_file="/a/1.mkv",
            parsed_title="A",
            parse_group="A",
            tmdb_korean_title_group="한글 제목",
            tmdb_series_id="",
            tmdb_poster_path="",
            tmdb_backdrop_path="",
            year="",
            season="",
            resolution="1080p",
            status="스캔됨",
            poster_url="",
            backdrop_url="",
            target_path="",
        ),
        PipelineRow(
            original_file="/a/2.mkv",
            parsed_title="A",
            parse_group="A",
            tmdb_korean_title_group="한글 제목",
            tmdb_series_id="",
            tmdb_poster_path="",
            tmdb_backdrop_path="",
            year="",
            season="",
            resolution="1080p",
            status="스캔됨",
            poster_url="",
            backdrop_url="",
            target_path="",
        ),
    ]
    ok = model.update_rows_if_compatible(group_pipeline_rows(updated))

    assert ok is True
    assert model.modelReset.call_count == 0
    assert spy.calls >= 1

