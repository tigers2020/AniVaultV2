from __future__ import annotations

from pathlib import Path
from threading import Event

from anivault.application.dto.plan import ApplyInput
from anivault.application.use_cases.apply_plan import (
    _apply_operations_or_error,
    _execute_apply,
    _move_operation_or_error,
)
from anivault.domain.models.file_operation import FileOperation, OperationType


class _FileRepo:
    def __init__(self, *, move_error: OSError | None = None) -> None:
        self.moves: list[tuple[Path, Path]] = []
        self.pruned: list[Path] = []
        self._move_error = move_error

    def move(self, src: Path, dest: Path) -> None:
        if self._move_error is not None:
            raise self._move_error
        self.moves.append((src, dest))

    def prune_empty_dirs_under(self, root: Path) -> None:
        self.pruned.append(root)


class _LibraryIndex:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str, str]] = []

    def relocate_media_file(
        self,
        root_id: int,
        old_absolute_path: str,
        new_absolute_path: str,
    ) -> None:
        self.calls.append((root_id, old_absolute_path, new_absolute_path))


class _OperationLog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save_plan(self, operations: list[object]) -> Path:
        return self.path


class _OrganizePlan:
    def __init__(self) -> None:
        self.plan_statuses: list[tuple[int, str]] = []
        self.item_statuses: list[tuple[int, str]] = []
        self.log_paths: list[tuple[int, str | None]] = []

    def update_plan_status(self, plan_id: int, status: str) -> None:
        self.plan_statuses.append((plan_id, status))

    def update_item_status(self, item_id: int, status: str) -> None:
        self.item_statuses.append((item_id, status))

    def set_plan_fs_log_path(self, plan_id: int, path: str | None) -> None:
        self.log_paths.append((plan_id, path))


def _op(name: str) -> FileOperation:
    return FileOperation(OperationType.MOVE, f"/src/{name}.mkv", f"/dest/{name}.mkv")


def test_move_operation_or_error_updates_library_index() -> None:
    repo = _FileRepo()
    index = _LibraryIndex()

    moved, error = _move_operation_or_error(repo, index, 7, _op("episode"))

    assert error is None
    assert moved == (str(Path("/src/episode.mkv")), str(Path("/dest/episode.mkv")))
    assert index.calls == [(7, str(Path("/src/episode.mkv")), str(Path("/dest/episode.mkv")))]


def test_apply_operations_or_error_stops_on_cancel() -> None:
    repo = _FileRepo()
    organize_plan = _OrganizePlan()
    token = Event()
    token.set()

    result = _apply_operations_or_error(
        ops=[_op("a")],
        file_repo=repo,
        library_index=None,
        root_idx=None,
        organize_plan=organize_plan,
        plan_id=11,
        item_ids=[101],
        progress_callback=None,
        cancel_token=token,
        log_path=Path("/logs/plan.log"),
    )

    assert result is not None
    assert result.error == "취소되었습니다."
    assert organize_plan.plan_statuses == [(11, "failed")]


def test_apply_operations_or_error_marks_failure() -> None:
    repo = _FileRepo(move_error=OSError("disk full"))
    organize_plan = _OrganizePlan()

    result = _apply_operations_or_error(
        ops=[_op("a")],
        file_repo=repo,
        library_index=None,
        root_idx=None,
        organize_plan=organize_plan,
        plan_id=12,
        item_ids=[201],
        progress_callback=None,
        cancel_token=Event(),
        log_path=Path("/logs/plan.log"),
    )

    assert result is not None
    assert result.error == "disk full"
    assert organize_plan.item_statuses == [(201, "failed")]
    assert organize_plan.plan_statuses == [(12, "failed")]


def test_execute_apply_returns_validation_errors_for_empty_inputs() -> None:
    repo = _FileRepo()

    result = _execute_apply(
        ApplyInput(operations=(), dry_run=False, log_root=""),
        None,
        Event(),
        file_repo=repo,
        operation_log_factory=lambda root: _OperationLog(root / "plan.log"),
    )

    assert result.error == "적용할 작업이 없습니다."


def test_execute_apply_dry_run_saves_log_without_moving() -> None:
    repo = _FileRepo()
    organize_plan = _OrganizePlan()

    result = _execute_apply(
        ApplyInput(
            operations=(_op("a"),),
            dry_run=True,
            log_root="/logs",
            organize_plan_id=1,
            organize_item_ids=(9,),
        ),
        None,
        Event(),
        file_repo=repo,
        operation_log_factory=lambda root: _OperationLog(root / "plan.log"),
        organize_plan=organize_plan,
    )

    assert result.error is None
    assert result.moved_count == 0
    assert repo.moves == []
    assert organize_plan.log_paths == []


def test_execute_apply_updates_plan_and_prunes_dirs_after_success() -> None:
    repo = _FileRepo()
    organize_plan = _OrganizePlan()
    progress_events: list[tuple[int, int, str]] = []

    result = _execute_apply(
        ApplyInput(
            operations=(_op("a"), _op("b")),
            dry_run=False,
            log_root="/logs",
            source_root="/source",
            index_root_id=5,
            organize_plan_id=77,
            organize_item_ids=(1, 2),
        ),
        lambda event: progress_events.append((event.current, event.total, event.item_path or "")),
        Event(),
        file_repo=repo,
        operation_log_factory=lambda root: _OperationLog(root / "plan.log"),
        library_index=_LibraryIndex(),
        organize_plan=organize_plan,
    )

    assert result.error is None
    assert result.moved_count == 2
    assert organize_plan.log_paths == [(77, str(Path("/logs/plan.log")))]
    assert organize_plan.item_statuses == [(1, "applied"), (2, "applied")]
    assert organize_plan.plan_statuses == [(77, "applied")]
    assert repo.pruned == [Path("/source")]
    assert progress_events[-1] == (2, 2, str(Path("/dest/b.mkv")))
