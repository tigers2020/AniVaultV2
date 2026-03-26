"""sqlite_title_match_repository.py

TitleMatchRepository SQLite 구현.

Author: Pom Kim
"""

from __future__ import annotations

import json
import logging
import sqlite3
from threading import Lock

from anivault.adapters.persistence.sqlite.sqlite_time import (
    is_utc_sqlite_text_expired,
    utc_now_sqlite_text,
)
from anivault.application.dto.title_match import GroupTmdbMatchRecord, MatchStatusDto
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO

logger = logging.getLogger(__name__)

_SEARCH_CACHE_UPSERT = """
INSERT INTO tmdb_search_cache (
    cache_key, language, normalized_query, year_hint, page,
    response_json, expires_at, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(cache_key) DO UPDATE SET
    language = excluded.language,
    normalized_query = excluded.normalized_query,
    year_hint = excluded.year_hint,
    page = excluded.page,
    response_json = excluded.response_json,
    expires_at = excluded.expires_at
"""

_SERIES_UPSERT = """
INSERT INTO tmdb_series (
    tmdb_id, name_ko, original_name, poster_path, raw_json,
    expires_at, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(tmdb_id) DO UPDATE SET
    name_ko = excluded.name_ko,
    original_name = excluded.original_name,
    poster_path = excluded.poster_path,
    raw_json = excluded.raw_json,
    expires_at = excluded.expires_at,
    updated_at = excluded.updated_at
"""

_GROUP_MATCH_UPSERT = """
INSERT INTO group_tmdb_matches (
    group_id, tmdb_id, match_status, match_score, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(group_id) DO UPDATE SET
    tmdb_id = excluded.tmdb_id,
    match_status = excluded.match_status,
    match_score = excluded.match_score,
    updated_at = excluded.updated_at
"""


class SqliteTitleMatchRepository:
    """tmdb_search_cache·tmdb_series·group_tmdb_matches."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        """연결과 직렬화 Lock을 받는다.

        Args:
            self: 저장소.
            conn: 공유 SQLite 연결.
            lock: 메서드 단위 락.

        Returns:
            None.
        """
        self._conn = conn
        self._lock = lock

    def get_search_cache_json(self, cache_key: str) -> str | None:
        """미만료 검색 캐시 JSON 문자열을 반환한다.

        Args:
            self: 저장소.
            cache_key: 캐시 키.

        Returns:
            JSON 문자열. miss·만료 시 None.
        """
        k = (cache_key or "").strip()
        if not k:
            return None
        with self._lock:
            cur = self._conn.execute(
                "SELECT response_json, expires_at FROM tmdb_search_cache WHERE cache_key = ?",
                (k,),
            )
            row = cur.fetchone()
            self._conn.commit()
        if row is None:
            return None
        js, exp = str(row[0]), str(row[1])
        if is_utc_sqlite_text_expired(exp):
            return None
        return js

    def put_search_cache(
        self,
        cache_key: str,
        *,
        language: str,
        normalized_query: str,
        year_hint: int | None,
        page: int,
        response_json: str,
        expires_at: str,
    ) -> None:
        """검색 캐시를 덮어쓴다.

        Args:
            self: 저장소.
            cache_key: PRIMARY KEY.
            language: API 언어.
            normalized_query: 정규화된 검색어.
            year_hint: 연도. None이면 SQL NULL.
            page: 페이지.
            response_json: JSON 본문.
            expires_at: 만료 시각.

        Returns:
            None.
        """
        k = (cache_key or "").strip()
        if not k:
            return
        now = utc_now_sqlite_text()
        with self._lock:
            try:
                self._conn.execute(
                    _SEARCH_CACHE_UPSERT,
                    (
                        k,
                        language,
                        normalized_query,
                        year_hint,
                        int(page),
                        response_json,
                        expires_at,
                        now,
                    ),
                )
                self._conn.commit()
            except sqlite3.Error as e:
                logger.warning("tmdb_search_cache put 실패 cache_key=%s: %s", k, e)
                self._conn.rollback()
                raise

    def invalidate_search(self, cache_key: str) -> None:
        """단일 캐시 키 행을 삭제한다.

        Args:
            self: 저장소.
            cache_key: 완성된 키.

        Returns:
            None.
        """
        k = (cache_key or "").strip()
        if not k:
            return
        with self._lock:
            self._conn.execute("DELETE FROM tmdb_search_cache WHERE cache_key = ?", (k,))
            self._conn.commit()

    def upsert_series(
        self,
        candidate: TmdbSeriesCandidateDTO,
        *,
        raw_json: str,
        expires_at: str,
    ) -> None:
        """시리즈 스냅샷을 저장한다.

        Args:
            self: 저장소.
            candidate: 핫 필드.
            raw_json: 원문 JSON.
            expires_at: 만료.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        tid = int(candidate.tmdb_id)
        with self._lock:
            try:
                self._conn.execute(
                    _SERIES_UPSERT,
                    (
                        tid,
                        (candidate.name_ko or "").strip(),
                        (candidate.original_name or "").strip(),
                        (candidate.poster_path or "").strip(),
                        raw_json,
                        expires_at,
                        now,
                        now,
                    ),
                )
                self._conn.commit()
            except sqlite3.Error as e:
                logger.warning("tmdb_series upsert 실패 tmdb_id=%s: %s", tid, e)
                self._conn.rollback()
                raise

    def get_series_candidate(self, tmdb_id: int) -> TmdbSeriesCandidateDTO | None:
        """미만료 시리즈 후보를 읽는다.

        Args:
            self: 저장소.
            tmdb_id: TMDB id.

        Returns:
            DTO. miss면 None.
        """
        with self._lock:
            cur = self._conn.execute(
                "SELECT raw_json, expires_at FROM tmdb_series WHERE tmdb_id = ?",
                (int(tmdb_id),),
            )
            row = cur.fetchone()
            self._conn.commit()
        if row is None:
            return None
        raw, exp = str(row[0]), str(row[1])
        if is_utc_sqlite_text_expired(exp):
            return None
        try:
            return _candidate_from_raw_json(raw)
        except (KeyError, OSError, TypeError, ValueError) as e:
            logger.warning("tmdb_series raw_json 역직렬화 실패 tmdb_id=%s: %s", tmdb_id, e)
            return None

    def get_group_match(self, group_id: int) -> GroupTmdbMatchRecord | None:
        """그룹 매칭 행을 조회한다.

        Args:
            self: 저장소.
            group_id: 그룹 id.

        Returns:
            레코드. 없으면 None.
        """
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT group_id, tmdb_id, match_status, match_score
                FROM group_tmdb_matches
                WHERE group_id = ?
                """,
                (int(group_id),),
            )
            row = cur.fetchone()
            self._conn.commit()
        if row is None:
            return None
        st = str(row[2])
        if st == "auto_matched":
            mst: MatchStatusDto = "auto_matched"
        elif st == "confirmed":
            mst = "confirmed"
        elif st == "rejected":
            mst = "rejected"
        else:
            return None
        return GroupTmdbMatchRecord(
            group_id=int(row[0]),
            tmdb_id=int(row[1]),
            match_status=mst,
            match_score=float(row[3]) if row[3] is not None else None,
        )

    def set_group_match(
        self,
        group_id: int,
        tmdb_id: int,
        match_status: MatchStatusDto,
        match_score: float | None,
    ) -> None:
        """그룹 매칭과 title_groups.tmdb_series_id를 갱신한다.

        Args:
            self: 저장소.
            group_id: title_groups.id.
            tmdb_id: TMDB 시리즈 id.
            match_status: 상태.
            match_score: 점수.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        gid = int(group_id)
        tid = int(tmdb_id)
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                self._conn.execute(
                    _GROUP_MATCH_UPSERT,
                    (gid, tid, match_status, match_score, now, now),
                )
                if match_status == "rejected":
                    self._conn.execute(
                        """
                        UPDATE title_groups
                        SET tmdb_series_id = NULL, updated_at = ?
                        WHERE id = ?
                        """,
                        (now, gid),
                    )
                else:
                    self._conn.execute(
                        """
                        UPDATE title_groups
                        SET tmdb_series_id = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (tid, now, gid),
                    )
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def invalidate_group_match(self, group_id: int) -> None:
        """그룹 매칭을 지우고 title_groups TMDB id를 비운다.

        Args:
            self: 저장소.
            group_id: title_groups.id.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        gid = int(group_id)
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                self._conn.execute(
                    "DELETE FROM group_tmdb_matches WHERE group_id = ?",
                    (gid,),
                )
                self._conn.execute(
                    """
                    UPDATE title_groups
                    SET tmdb_series_id = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (now, gid),
                )
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise


def _candidate_from_raw_json(raw: str) -> TmdbSeriesCandidateDTO:
    """raw_json에서 TmdbSeriesCandidateDTO를 만든다.

    Args:
        raw: compact JSON 객체 문자열.

    Returns:
        DTO.

    Raises:
        (KeyError, TypeError, ValueError): 필드 불충분.
    """
    data = json.loads(raw)
    if not isinstance(data, dict):
        msg = "raw_json은 객체여야 한다"
        raise TypeError(msg)
    return TmdbSeriesCandidateDTO(
        tmdb_id=int(data["tmdb_id"]),
        name_ko=str(data.get("name_ko", "") or ""),
        original_name=str(data.get("original_name", "") or ""),
        first_air_date=str(data.get("first_air_date", "") or ""),
        original_language=str(data.get("original_language", "") or ""),
        overview=str(data.get("overview", "") or ""),
        poster_path=str(data.get("poster_path", "") or ""),
        backdrop_path=str(data.get("backdrop_path", "") or ""),
        popularity=float(data.get("popularity", 0.0) or 0.0),
    )
