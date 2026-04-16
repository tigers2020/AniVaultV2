from __future__ import annotations

import json
from pathlib import Path

import pytest

from anivault.adapters.operation_log.fs_operation_log import FsOperationLogRepository
from anivault.constants.adapters.operation_log import OPERATION_LOG_JSON_ARRAY_ERROR
from anivault.domain.models.file_operation import FileOperation, OperationType


def test_save_plan_serializes_file_operations_and_raw_objects(tmp_path: Path) -> None:
    repo = FsOperationLogRepository(log_dir=tmp_path)

    path = repo.save_plan(
        [
            FileOperation(OperationType.MOVE, "a", "b"),
            {"operation_type": "COPY", "source_path": "c", "destination_path": "d"},
            object(),
        ]
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.parent == tmp_path
    assert payload[0]["operation_type"] == "MOVE"
    assert payload[1]["operation_type"] == "COPY"
    assert "raw" in payload[2]


def test_load_plan_restores_operations_and_skips_non_dict_entries(tmp_path: Path) -> None:
    repo = FsOperationLogRepository(log_dir=tmp_path)
    log_path = tmp_path / "plan.log"
    log_path.write_text(
        json.dumps(
            [
                {"operation_type": "MOVE", "source_path": "a", "destination_path": "b"},
                {"operation_type": "copy", "source_path": "c", "destination_path": "d"},
                "skip-me",
            ]
        ),
        encoding="utf-8",
    )

    items = repo.load_plan(log_path)

    assert items == [
        FileOperation(OperationType.MOVE, "a", "b"),
        FileOperation(OperationType.COPY, "c", "d"),
    ]


def test_load_plan_requires_json_array(tmp_path: Path) -> None:
    repo = FsOperationLogRepository(log_dir=tmp_path)
    log_path = tmp_path / "broken.log"
    log_path.write_text('{"not": "a list"}', encoding="utf-8")

    with pytest.raises(ValueError, match=OPERATION_LOG_JSON_ARRAY_ERROR):
        repo.load_plan(log_path)
