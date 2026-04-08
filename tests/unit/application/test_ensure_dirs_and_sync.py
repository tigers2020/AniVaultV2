from __future__ import annotations

from pathlib import Path
from threading import Event

from anivault.application.dto.title_groups import TitleGroupMemberSync
from anivault.application.use_cases.ensure_plan_directories import EnsureDirsInput, execute
from anivault.application.use_cases.sync_title_groups import _computed_to_bundle, make_execute
from anivault.domain.models.file_operation import FileOperation, OperationType
from anivault.domain.services.title_grouping import TitleGroupComputed, TitleGroupMemberComputed


def _move(dest: Path) -> FileOperation:
    return FileOperation(OperationType.MOVE, "/src/file.mkv", str(dest))


def test_ensure_plan_directories_returns_error_for_empty_input() -> None:
    result = execute(EnsureDirsInput(operations=()), None, Event())

    assert result.error == "작업이 없습니다."


def test_ensure_plan_directories_stops_on_cancel(tmp_path: Path) -> None:
    token = Event()
    token.set()

    result = execute(EnsureDirsInput(operations=(_move(tmp_path / "A" / "file.mkv"),)), None, token)

    assert result.error == "취소되었습니다."
    assert result.created_count == 0


def test_ensure_plan_directories_creates_directories_and_reports_progress(tmp_path: Path) -> None:
    events = []

    result = execute(
        EnsureDirsInput(
            operations=(
                _move(tmp_path / "A" / "one.mkv"),
                _move(tmp_path / "B" / "two.mkv"),
            )
        ),
        events.append,
        Event(),
    )

    assert result.error is None
    assert result.created_count == 2
    assert (tmp_path / "A").is_dir()
    assert (tmp_path / "B").is_dir()
    assert [(e.current, e.total) for e in events] == [(1, 2), (2, 2)]


def test_ensure_plan_directories_returns_os_error(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("boom")))

    result = execute(EnsureDirsInput(operations=(_move(tmp_path / "A" / "one.mkv"),)), None, Event())

    assert result.error == "boom"


def test_computed_to_bundle_maps_domain_result() -> None:
    bundle = _computed_to_bundle(
        TitleGroupComputed(
            group_key="group",
            group_type="parsed_title_norm",
            canonical_title="Show",
            canonical_title_normalized="show",
            members=(TitleGroupMemberComputed(1, "primary_video", 0.9),),
        )
    )

    assert bundle.group_key == "group"
    assert bundle.members == (TitleGroupMemberSync(1, "primary_video", 0.9),)


def test_make_execute_loads_rows_computes_groups_and_replaces(monkeypatch) -> None:
    class _Repo:
        def __init__(self) -> None:
            self.replaced = None

        def load_rows_for_grouping(self, root_id: int):
            return ["row"]

        def replace_root_title_groups(self, root_id: int, bundles):
            self.replaced = (root_id, bundles)

    repo = _Repo()
    computed = [
        TitleGroupComputed(
            group_key="group",
            group_type="parsed_title_norm",
            canonical_title="Show",
            canonical_title_normalized="show",
            members=(TitleGroupMemberComputed(1, "primary_video", 0.9),),
        )
    ]
    monkeypatch.setattr(
        "anivault.application.use_cases.sync_title_groups.compute_title_groups",
        lambda rows: computed,
    )

    make_execute(repo)(7)

    assert repo.replaced is not None
    root_id, bundles = repo.replaced
    assert root_id == 7
    assert len(bundles) == 1
