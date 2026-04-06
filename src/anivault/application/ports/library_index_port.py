"""library_index_port.py

스캔 결과를 SQLite 인덱스에 반영하는 포트.

Author: Pom Kim
"""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from anivault.application.dto.library_index import IndexedMediaForParse, MediaFileRecord

ScanSessionStatus = Literal["success", "failed", "cancelled"]


@runtime_checkable
class LibraryIndexRepository(Protocol):
    """라이브러리 루트·스캔 세션·미디어 파일 인덱스 계약."""

    def upsert_root(self, root_path: str, *, display_name: str | None = None) -> int:
        """루트를 등록하거나 갱신하고 `library_roots.id`를 반환한다.

        Args:
            self: 저장소.
            root_path: 스캔 루트 경로(절대 권장).
            display_name: 표시명. None이면 기존 값 유지(업서트 시).

        Returns:
            루트 행 ID.
        """
        ...

    def begin_scan(self, root_id: int, scan_kind: str) -> int:
        """상태 `running` 인 스캔 세션을 만들고 세션 ID를 반환한다.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            scan_kind: 예: `full`, `incremental`.

        Returns:
            `scan_sessions.id`.
        """
        ...

    def finish_scan(
        self,
        session_id: int,
        *,
        status: ScanSessionStatus,
        files_seen: int,
        files_added: int,
        files_updated: int,
        files_removed: int,
        error_message: str | None = None,
    ) -> None:
        """스캔 세션을 종료 상태로 갱신한다.

        Args:
            self: 저장소.
            session_id: `scan_sessions.id`.
            status: `success`, `failed`, `cancelled`.
            files_seen: 이번 스캔에서 처리한 파일 수.
            files_added: 신규 `media_files` 행 수.
            files_updated: 기존 행 갱신 수.
            files_removed: `mark_missing_deleted` 등으로 soft-delete된 수.
            error_message: 실패 시 메시지.

        Returns:
            None.
        """
        ...

    def upsert_media_file(
        self,
        root_id: int,
        session_id: int,
        *,
        absolute_path: str,
        media_kind: str,
    ) -> tuple[bool, bool]:
        """단일 파일 메타를 반영한다(`is_deleted=0`으로 복귀).

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            session_id: 현재 스캔 세션 ID.
            absolute_path: 파일 절대 경로.
            media_kind: `video`, `subtitle` 등.

        Returns:
            `(is_new, is_updated)` — 신규 삽입이면 `(True, False)`, 기존 갱신이면 `(False, True)`.
        """
        ...

    def mark_missing_deleted(self, root_id: int, session_id: int, seen_path_norms: set[str]) -> int:
        """이번 스캔에 나타나지 않은 기존 행을 `is_deleted=1`로 표시한다.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            session_id: 스캔 세션 ID(로깅·확장용; 쿼리에 반드시 쓰지는 않음).
            seen_path_norms: 이번 스캔에서 본 `path_norm` 집합.

        Returns:
            soft-delete된 행 수.
        """
        ...

    def resolve_media_for_parse(
        self,
        root_id: int,
        absolute_paths: list[str],
    ) -> list[IndexedMediaForParse | None]:
        """절대 경로 목록에 대응하는 인덱스 메타를 **입력과 동일 길이·순서**로 반환한다.

        동일 path가 중복되어도 허용하며, 각 슬롯은 같은 행을 가리킬 수 있다.
        `root_id` 범위 밖이거나 `is_deleted=1`이면 해당 슬롯은 None.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            absolute_paths: 스캔·파싱 파이프라인 경로(절대 경로 문자열).

        Returns:
            `IndexedMediaForParse` 또는 None의 리스트.
        """
        ...

    def list_media_by_root(
        self,
        root_id: int,
        *,
        include_deleted: bool = False,
    ) -> list[MediaFileRecord]:
        """루트 소속 미디어 행을 조회한다.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            include_deleted: True면 삭제 표시된 행도 포함.

        Returns:
            `MediaFileRecord` 목록.
        """
        ...

    def relocate_media_file(
        self,
        root_id: int,
        *,
        old_absolute_path: str,
        new_absolute_path: str,
    ) -> bool:
        """파일 이동 반영: 동일 행(id·media_kind 등 유지)에 경로·크기·mtime만 갱신.

        `old_absolute_path`에 해당하는 행이 없으면 False(스킵).

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            old_absolute_path: 이동 직전 절대 경로.
            new_absolute_path: 이동 직후 절대 경로.

        Returns:
            행을 갱신했으면 True, 대상 없음이면 False.
        """
        ...

    def relocate_media_files(
        self,
        root_id: int,
        *,
        pairs: tuple[tuple[str, str], ...],
    ) -> None:
        """`relocate_media_file`를 순서대로 호출한다.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            pairs: `(old_absolute_path, new_absolute_path)` 들.

        Returns:
            None.
        """
        ...
