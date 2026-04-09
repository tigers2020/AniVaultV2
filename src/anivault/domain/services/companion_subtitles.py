"""companion_subtitles.py

비디오와 같은 디렉터리·같은 stem 의 자막 파일을 찾아 이동 작업으로 만든다.

추가 확장자는 이후 설정(path_rules 등)으로 확장할 수 있다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from anivault.domain.media.extensions import SUBTITLE_EXTENSIONS
from anivault.domain.models import FileOperation, OperationType


def companion_subtitle_operations(
    video_source: str,
    video_destination: str,
    *,
    directory_entries: Sequence[Path] | None = None,
) -> list[FileOperation]:
    """비디오와 동일 stem 의 자막 파일에 대한 MOVE 작업 목록을 반환한다.

    같은 부모 폴더에서 stem 이 비디오 파일명과 같고, 확장자가 SUBTITLE_EXTENSIONS 에
    속하는 일반 파일만 포함한다. 비디오 본인 경로는 제외한다.

    Args:
        video_source: 비디오 원본 절대 경로.
        video_destination: 비디오 목적지 절대 경로.
        directory_entries: 이미 읽은 부모 디렉터리 엔트리. None이면 parent 에서 iterdir.

    Returns:
        자막별 FileOperation 목록. iterdir 실패 시 빈 목록.
    """
    video_path = Path(video_source)
    dest_parent = Path(video_destination).parent
    stem = video_path.stem
    parent = video_path.parent

    if directory_entries is not None:
        entries = list(directory_entries)
    else:
        try:
            entries = list(parent.iterdir())
        except OSError:
            return []

    out: list[FileOperation] = []
    for child in entries:
        if not child.is_file():
            continue
        if child == video_path:
            continue
        if child.stem != stem:
            continue
        suffix = child.suffix.lower()
        if suffix not in SUBTITLE_EXTENSIONS:
            continue
        dest = dest_parent / child.name
        out.append(
            FileOperation(
                operation_type=OperationType.MOVE,
                source_path=str(child),
                destination_path=str(dest),
            )
        )
    return out
