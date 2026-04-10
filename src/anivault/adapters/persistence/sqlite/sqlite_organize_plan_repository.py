"""sqlite_organize_plan_repository.py

`OrganizePlanRepository` SQLite 구현.

Author: Pom Kim
"""

from __future__ import annotations

import sqlite3
from threading import Lock

from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.contracts.organize_plan import (
    OrganizeOperationKind,
    OrganizePlanAppendRow,
    OrganizePlanBundle,
    OrganizePlanHeaderRecord,
    OrganizePlanItemRecord,
    OrganizePlanItemStatus,
    OrganizePlanListEntry,
    OrganizePlanStatus,
)


def _parse_plan_status(value: object) -> OrganizePlanStatus:
    text = str(value)
    if text == "draft":
        return "draft"
    if text == "previewed":
        return "previewed"
    if text == "applied":
        return "applied"
    if text == "failed":
        return "failed"
    if text == "rolled_back":
        return "rolled_back"
    msg = f"Unknown organize plan status: {text}"
    raise ValueError(msg)


def _parse_item_status(value: object) -> OrganizePlanItemStatus:
    text = str(value)
    if text == "pending":
        return "pending"
    if text == "applied":
        return "applied"
    if text == "skipped":
        return "skipped"
    if text == "failed":
        return "failed"
    if text == "rolled_back":
        return "rolled_back"
    msg = f"Unknown organize plan item status: {text}"
    raise ValueError(msg)


def _parse_operation_kind(value: object) -> OrganizeOperationKind:
    text = str(value)
    if text == "move":
        return "move"
    if text == "rename":
        return "rename"
    if text == "copy":
        return "copy"
    if text == "link":
        return "link"
    msg = f"Unknown organize operation kind: {text}"
    raise ValueError(msg)


class SqliteOrganizePlanRepository:
    """정리 플랜 SQLite 저장소."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        """연결과 스레드 직렬화용 Lock을 받는다.

        Args:
            self: 저장소.
            conn: 공유 SQLite 연결.
            lock: 메서드 단위 직렬화용 락.

        Returns:
            None.
        """
        self._conn = conn
        self._lock = lock

    def create_plan(
        self,
        root_id: int,
        plan_status: OrganizePlanStatus,
        summary_json: str,
        *,
        fs_log_path: str | None = None,
    ) -> int:
        """플랜 헤더를 추가하고 id를 반환한다.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            plan_status: 초기 상태.
            summary_json: 요약 JSON.
            fs_log_path: 로그 경로.

        Returns:
            새 플랜 ID.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO organize_plans (
                    root_id, plan_status, summary_json, fs_log_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (root_id, plan_status, summary_json, fs_log_path, now, now),
            )
            row = cur.fetchone()
            self._conn.commit()
        assert row is not None
        return int(row[0])

    def append_items(
        self,
        plan_id: int,
        rows: tuple[OrganizePlanAppendRow, ...],
    ) -> tuple[int, ...]:
        """아이템을 한 트랜잭션에서 배치 삽입하고 id 목록을 반환한다.

        Args:
            self: 저장소.
            plan_id: 플랜 ID.
            rows: 삽입 행.

        Returns:
            삽입 순서와 동일한 id들.
        """
        if not rows:
            return ()
        now = utc_now_sqlite_text()
        with self._lock:
            cur = self._conn.execute(
                "SELECT id FROM organize_plan_items WHERE plan_id = ? ORDER BY id ASC",
                (plan_id,),
            )
            before_count = len(cur.fetchall())
            self._conn.executemany(
                """
                INSERT INTO organize_plan_items (
                    plan_id, src_path_norm, dst_path_norm, operation_kind, status, detail_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                [
                    (
                        plan_id,
                        r.src_path_norm,
                        r.dst_path_norm,
                        r.operation_kind,
                        r.detail_json,
                        now,
                        now,
                    )
                    for r in rows
                ],
            )
            cur = self._conn.execute(
                "SELECT id FROM organize_plan_items WHERE plan_id = ? ORDER BY id ASC",
                (plan_id,),
            )
            after_ids = [int(r[0]) for r in cur.fetchall()]
            self._conn.commit()
        new_ids = after_ids[before_count:]
        return tuple(new_ids)

    def update_plan_status(
        self,
        plan_id: int,
        plan_status: OrganizePlanStatus,
    ) -> None:
        """플랜 상태를 갱신한다.

        Args:
            self: 저장소.
            plan_id: 플랜 ID.
            plan_status: 새 상태.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            self._conn.execute(
                "UPDATE organize_plans SET plan_status = ?, updated_at = ? WHERE id = ?",
                (plan_status, now, plan_id),
            )
            self._conn.commit()

    def update_item_status(
        self,
        item_id: int,
        status: OrganizePlanItemStatus,
    ) -> None:
        """아이템 상태를 갱신한다.

        Args:
            self: 저장소.
            item_id: 아이템 ID.
            status: 새 상태.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            self._conn.execute(
                "UPDATE organize_plan_items SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, item_id),
            )
            self._conn.commit()

    def set_plan_fs_log_path(
        self,
        plan_id: int,
        fs_log_path: str | None,
    ) -> None:
        """Fs 로그 경로를 설정한다.

        Args:
            self: 저장소.
            plan_id: 플랜 ID.
            fs_log_path: 경로.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            self._conn.execute(
                "UPDATE organize_plans SET fs_log_path = ?, updated_at = ? WHERE id = ?",
                (fs_log_path, now, plan_id),
            )
            self._conn.commit()

    def load_plan(self, plan_id: int) -> OrganizePlanBundle | None:
        """플랜과 아이템을 조회한다. 아이템은 id 오름차순.

        Args:
            self: 저장소.
            plan_id: 플랜 ID.

        Returns:
            번들 또는 None.
        """
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT id, root_id, plan_status, summary_json, fs_log_path, created_at, updated_at
                FROM organize_plans WHERE id = ?
                """,
                (plan_id,),
            )
            hr = cur.fetchone()
            if hr is None:
                self._conn.commit()
                return None
            cur = self._conn.execute(
                """
                SELECT id, plan_id, src_path_norm, dst_path_norm, operation_kind, status, detail_json,
                       created_at, updated_at
                FROM organize_plan_items WHERE plan_id = ? ORDER BY id ASC
                """,
                (plan_id,),
            )
            item_rows = cur.fetchall()
            self._conn.commit()
        header = OrganizePlanHeaderRecord(
            id=int(hr[0]),
            root_id=int(hr[1]),
            plan_status=_parse_plan_status(hr[2]),
            summary_json=str(hr[3]),
            fs_log_path=str(hr[4]) if hr[4] is not None else None,
            created_at=str(hr[5]),
            updated_at=str(hr[6]),
        )
        items: list[OrganizePlanItemRecord] = []
        for ir in item_rows:
            items.append(
                OrganizePlanItemRecord(
                    id=int(ir[0]),
                    plan_id=int(ir[1]),
                    src_path_norm=str(ir[2]),
                    dst_path_norm=str(ir[3]),
                    operation_kind=_parse_operation_kind(ir[4]),
                    status=_parse_item_status(ir[5]),
                    detail_json=str(ir[6]) if ir[6] is not None else None,
                    created_at=str(ir[7]),
                    updated_at=str(ir[8]),
                )
            )
        return OrganizePlanBundle(header=header, items=tuple(items))

    def list_plans_for_root(
        self,
        root_id: int,
        *,
        limit: int = 100,
    ) -> tuple[OrganizePlanListEntry, ...]:
        """루트별 플랜 목록.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            limit: 최대 개수.

        Returns:
            엔트리들.
        """
        lim = max(1, min(int(limit), 10_000))
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT id, plan_status, created_at, updated_at
                FROM organize_plans
                WHERE root_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (root_id, lim),
            )
            rows = cur.fetchall()
            self._conn.commit()
        out: list[OrganizePlanListEntry] = []
        for r in rows:
            out.append(
                OrganizePlanListEntry(
                    id=int(r[0]),
                    plan_status=_parse_plan_status(r[1]),
                    created_at=str(r[2]),
                    updated_at=str(r[3]),
                )
            )
        return tuple(out)

    def mark_plan_rolled_back(self, plan_id: int) -> None:
        """플랜·소속 아이템을 rolled_back으로 맞춘다.

        Args:
            self: 저장소.
            plan_id: 플랜 ID.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            self._conn.execute(
                "UPDATE organize_plans SET plan_status = 'rolled_back', updated_at = ? WHERE id = ?",
                (now, plan_id),
            )
            self._conn.execute(
                "UPDATE organize_plan_items SET status = 'rolled_back', updated_at = ? WHERE plan_id = ?",
                (now, plan_id),
            )
            self._conn.commit()
