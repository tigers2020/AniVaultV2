"""match_series.py

파싱된 파일 그룹을 TMDB TV 시리즈에 매칭하고 한글 표시 제목을 채운다.

Author: Pom Kim
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from threading import Event

from anivault.application.dto.match_result import (
    GroupMatchResultDTO,
    MatchFileRow,
    MatchInput,
    MatchResult,
)
from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.rules.tmdb_image_url import tmdb_backdrop_cdn_url, tmdb_poster_cdn_url
from anivault.domain.rules.tmdb_search_query import (
    compact_compare_key,
    iter_strip_last_word_chain,
    iter_tmdb_search_queries,
)

_MAX_CANDIDATES = 5

MatchProgressCallback = Callable[[ProgressEvent], None]

logger = logging.getLogger(__name__)


def _utc_plus_days_iso_z(days: int) -> str:
    """UTC 기준 만료 시각 문자열(`…Z`)을 만든다.

    Args:
        days: 더할 일 수.

    Returns:
        SQLite·정책과 동일한 ISO 텍스트.
    """
    return (datetime.now(UTC) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _group_key(row: MatchFileRow) -> str:
    """매칭 그룹 키를 행에서 뽑는다.

    Args:
        row: 파일 한 줄 스냅샷.

    Returns:
        parse_group 우선, 없으면 parsed_title, 둘 다 없으면 original_file.
    """
    pg = (row.parse_group or "").strip()
    if pg:
        return pg
    pt = (row.parsed_title or "").strip()
    if pt:
        return pt
    return row.original_file


def _year_prefix(iso_date: str) -> str:
    """ISO 날짜 문자열에서 연도 4자리 접두를 반환한다.

    Args:
        iso_date: YYYY-MM-DD 형태 등.

    Returns:
        앞 4자리(연도). 길이 부족 시 빈 문자열.
    """
    d = (iso_date or "").strip()
    return d[:4] if len(d) >= 4 else ""


def _score_one_candidate(
    c: TmdbSeriesCandidateDTO,
    qn: str,
    expected_year: str,
    reason_in: str,
) -> tuple[float, str]:
    """단일 후보에 대한 점수와 갱신된 이유 문자열을 계산한다.

    Args:
        c: TMDB 시리즈 후보.
        qn: 정규화된 검색어.
        expected_year: 기대 방영 연도(빈 문자열이면 연도 보너스 없음).
        reason_in: 이전 후보까지 반영된 이유 문자열.

    Returns:
        (누적 점수, 이 후보 처리 후 이유 문자열).
    """
    score = 0.0
    reason = reason_in
    names = [compact_compare_key(c.name_ko), compact_compare_key(c.original_name)]
    names = [n for n in names if n]
    if qn and any(qn == n for n in names):
        score += 10.0
        reason = "exact_name"
    elif qn and any(qn in n or n in qn for n in names):
        score += 5.0
        reason = "partial_name"
    if (c.name_ko or "").strip():
        score += 2.0
    cy = _year_prefix(c.first_air_date)
    if expected_year and cy == expected_year:
        score += 3.0
        reason = f"{reason}+year"
    score += (c.popularity or 0.0) * 0.01
    return score, reason


def _select_best_candidate(
    candidates: list[TmdbSeriesCandidateDTO],
    query: str,
    expected_year: str,
) -> tuple[TmdbSeriesCandidateDTO | None, float, str]:
    """검색 후보 중 쿼리·연도에 가장 맞는 항목과 신뢰도를 고른다.

    Args:
        candidates: TMDB 후보 목록.
        query: 그룹 검색어.
        expected_year: 기대 방영 연도 문자열(빈 문자열 가능).

    Returns:
        (선택 후보 또는 None, confidence 0~1, 선택 이유 코드).
    """
    if not candidates:
        return None, 0.0, "no_results"
    qn = compact_compare_key(query)
    best: TmdbSeriesCandidateDTO | None = None
    best_score = -1.0
    reason = "fallback_first"
    for c in candidates[:_MAX_CANDIDATES]:
        score, reason = _score_one_candidate(c, qn, expected_year, reason)
        if score > best_score:
            best_score = score
            best = c
    if best is None:
        return candidates[0], 0.5, "first_result"
    conf = min(1.0, max(0.0, best_score / 15.0))
    return best, conf, reason


def _index_files_by_group_key(files: list[MatchFileRow]) -> dict[str, list[int]]:
    """파일 행을 그룹 키별 인덱스 목록으로 묶는다.

    Args:
        files: 전체 파일 행 목록.

    Returns:
        그룹 키 → 해당 행 인덱스 리스트.
    """
    key_to_indices: dict[str, list[int]] = {}
    for i, f in enumerate(files):
        key_to_indices.setdefault(_group_key(f), []).append(i)
    return key_to_indices


def _notify_match_progress_prepare(
    progress_callback: MatchProgressCallback | None,
    total: int,
) -> None:
    """매칭 단계 시작 진행 이벤트를 보낸다.

    Args:
        progress_callback: ProgressEvent를 받는 콜백. None이면 무시.
        total: 그룹 개수.

    Returns:
        None.
    """
    if not total:
        return
    if progress_callback is None:
        return
    progress_callback(
        ProgressEvent(
            stage="match",
            current=0,
            total=total,
            message="TMDB 매칭 준비…",
            percent=0,
        )
    )


def _notify_match_progress_step(
    progress_callback: MatchProgressCallback | None,
    total: int,
    current: int,
    message: str,
) -> None:
    """매칭 단계 중 진행 이벤트를 보낸다.

    Args:
        progress_callback: ProgressEvent를 받는 콜백. None이면 무시.
        total: 그룹 개수.
        current: 현재 처리 순번(1부터).
        message: 표시 메시지.

    Returns:
        None.
    """
    if not total:
        return
    if progress_callback is None:
        return
    pct = int(current * 100 / total) if total else 100
    progress_callback(
        ProgressEvent(
            stage="match",
            current=current,
            total=total,
            message=message,
            percent=pct,
        )
    )


def apply_tmdb_candidate_to_file_rows(
    files: list[MatchFileRow],
    indices: list[int],
    candidate: TmdbSeriesCandidateDTO,
) -> None:
    """TMDB 시리즈 후보로 지정 인덱스의 파일 행을 갱신한다(자동·수동 매칭 공통).

    Args:
        files: 전체 파일 행 목록(제자리 수정).
        indices: 갱신할 행 인덱스 목록.
        candidate: 선택된 TMDB 시리즈 후보.

    Returns:
        None.
    """
    korean = (candidate.name_ko or "").strip()
    poster_path_raw = (candidate.poster_path or "").strip()
    poster = tmdb_poster_cdn_url(poster_path_raw)
    backdrop_path_raw = (candidate.backdrop_path or "").strip()
    backdrop = tmdb_backdrop_cdn_url(backdrop_path_raw)
    tid = str(candidate.tmdb_id)
    tmdb_year = _year_prefix(candidate.first_air_date)
    _apply_tmdb_to_file_rows(
        files,
        indices,
        korean,
        poster_path_raw,
        backdrop_path_raw,
        poster,
        backdrop,
        tid,
        tmdb_year,
    )


def _apply_tmdb_to_file_rows(
    files: list[MatchFileRow],
    indices: list[int],
    korean: str,
    poster_path_raw: str,
    backdrop_path_raw: str,
    poster: str,
    backdrop: str,
    tid: str,
    tmdb_year: str,
) -> None:
    """선택된 TMDB 시리즈 메타로 그룹 내 파일 행을 갱신한다.

    Args:
        files: 전체 파일 행 목록(제자리 수정).
        indices: 같은 그룹 행 인덱스.
        korean: 한글 표시 제목(트림됨).
        poster_path_raw: 포스터 상대 경로(원본).
        backdrop_path_raw: 백드롭 상대 경로(원본).
        poster: 포스터 전체 URL.
        backdrop: 백드롭 전체 URL.
        tid: 시리즈 ID 문자열.
        tmdb_year: first_air_date에서 뽑은 연도 접두.

    Returns:
        None.
    """
    for idx in indices:
        prev = files[idx]
        files[idx] = MatchFileRow(
            original_file=prev.original_file,
            parsed_title=prev.parsed_title,
            parse_group=prev.parse_group,
            tmdb_korean_title_group=korean or prev.tmdb_korean_title_group,
            tmdb_series_id=tid,
            tmdb_poster_path=poster_path_raw or prev.tmdb_poster_path,
            tmdb_backdrop_path=backdrop_path_raw or prev.tmdb_backdrop_path,
            year=tmdb_year if tmdb_year else prev.year,
            season=prev.season,
            resolution=prev.resolution,
            status="TMDB 매칭됨" if korean else prev.status,
            poster_url=poster or prev.poster_url,
            backdrop_url=backdrop or prev.backdrop_url,
            target_path=prev.target_path,
            episode=prev.episode,
        )


def persist_manual_tmdb_selection(
    files: list[MatchFileRow],
    indices: list[int],
    chosen: TmdbSeriesCandidateDTO,
    *,
    root_id: int | None,
    representative_path_norm: str | None,
    title_match: TitleMatchRepository | None,
    title_groups: TitleGroupRepository | None,
) -> None:
    """수동 매칭 선택을 tmdb_series·(가능 시) group_tmdb_matches에 반영한다.

    `title_groups`에서 그룹 id를 못 찾아도 `tmdb_series`는 항상 갱신해
    로컬 DB 우선 검색·포스터 캐시에 반영된다.

    Args:
        files: 전체 파일 행(참조만).
        indices: 갱신된 그룹 행 인덱스.
        chosen: 선택된 시리즈 후보.
        root_id: 라이브러리 루트 id.
        representative_path_norm: 그룹 대표 파일 path_norm.
        title_match: TMDB 매칭 저장소.
        title_groups: title_groups 저장소.

    Returns:
        None.
    """
    if title_match is None or not indices or max(indices) >= len(files):
        return
    if not chosen.tmdb_id:
        return
    raw_json = json.dumps(asdict(chosen), ensure_ascii=False, separators=(",", ":"))
    exp = _utc_plus_days_iso_z(7)
    try:
        title_match.upsert_series(chosen, raw_json=raw_json, expires_at=exp)
    except Exception:
        logger.exception("수동 TMDB tmdb_series upsert 실패 tmdb_id=%s", chosen.tmdb_id)
        return
    if root_id is None or not representative_path_norm or title_groups is None:
        return
    gid = title_groups.get_group_id_for_path_norm(root_id, representative_path_norm)
    if gid is None:
        logger.warning(
            "수동 TMDB: title_groups에 대표 경로 없음 root_id=%s path_norm=%s",
            root_id,
            representative_path_norm,
        )
        return
    try:
        title_match.set_group_match(gid, int(chosen.tmdb_id), "confirmed", None)
    except Exception:
        logger.exception(
            "수동 TMDB group 매칭 영속 실패 group_id=%s tmdb_id=%s",
            gid,
            chosen.tmdb_id,
        )


def _try_series_from_title_match_db(
    *,
    root_id: int | None,
    representative_path_norm: str | None,
    title_match: TitleMatchRepository | None,
    title_groups: TitleGroupRepository | None,
) -> list[TmdbSeriesCandidateDTO] | None:
    """로컬 DB에 확정·자동 매칭이 있으면 해당 시리즈 후보 한 건만 반환한다.

    Args:
        root_id: 인덱스 루트. None이면 단축 경로 없음.
        representative_path_norm: 그룹 대표 파일 `path_norm`.
        title_match: TMDB 매칭 저장소.
        title_groups: 작품 그룹 저장소.

    Returns:
        단축 경로로 후보를 찾았으면 길이 1 목록. 아니면 None(호출 측에서 API 검색 계속).
    """
    if (
        root_id is None
        or not representative_path_norm
        or title_match is None
        or title_groups is None
    ):
        return None
    gid = title_groups.get_group_id_for_path_norm(root_id, representative_path_norm)
    if gid is None:
        return None
    gm = title_match.get_group_match(gid)
    if gm is None or gm.match_status not in ("auto_matched", "confirmed"):
        return None
    cand = title_match.get_series_candidate(gm.tmdb_id)
    if cand is None:
        return None
    return [cand]


def _search_series_via_provider(
    group_key: str,
    provider: MetadataProvider,
) -> list[TmdbSeriesCandidateDTO]:
    """변형 검색어·끝단어 제거 체인으로 포트 검색을 시도해 첫 비어 있지 않은 결과를 반환한다.

    Args:
        group_key: 파싱 그룹 식별 문자열.
        provider: 메타데이터 검색 포트.

    Returns:
        첫 비어 있지 않은 검색 결과. 없으면 빈 목록.
    """
    seen_attempts: set[str] = set()
    for q in iter_tmdb_search_queries(group_key):
        for attempt in iter_strip_last_word_chain(q):
            ak = attempt.lower()
            if ak in seen_attempts:
                continue
            seen_attempts.add(ak)
            raw_candidates = list(provider.search_series(attempt, year=None))
            if raw_candidates:
                return raw_candidates
    return []


def _search_series_candidates_for_group(
    group_key: str,
    provider: MetadataProvider,
    *,
    root_id: int | None = None,
    representative_path_norm: str | None = None,
    title_match: TitleMatchRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
) -> list[TmdbSeriesCandidateDTO]:
    """그룹 키에 대해 변형 검색어·끝단어 제거 체인으로 TMDB 후보를 찾는다.

    연도 필터는 쓰지 않는다(파일 연도와 TMDB 첫 방영 연도 불일치로 0건이 나오는 것을 피함).

    Args:
        group_key: 파싱 그룹 식별 문자열.
        provider: 메타데이터 검색 포트.
        root_id: 인덱스 루트. None이면 DB 단축 경로 없음.
        representative_path_norm: 그룹 대표 파일 `path_norm`.
        title_match: TMDB 매칭 저장소.
        title_groups: 작품 그룹 저장소.

    Returns:
        첫 비어 있지 않은 검색 결과. 없으면 빈 목록.
    """
    from_db = _try_series_from_title_match_db(
        root_id=root_id,
        representative_path_norm=representative_path_norm,
        title_match=title_match,
        title_groups=title_groups,
    )
    if from_db is not None:
        return from_db
    return _search_series_via_provider(group_key, provider)


def _match_single_group_search_phase(
    group_key: str,
    provider: MetadataProvider,
    *,
    root_id: int | None = None,
    representative_path_norm: str | None = None,
    title_match: TitleMatchRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
) -> tuple[GroupMatchResultDTO, TmdbSeriesCandidateDTO | None]:
    """한 그룹에 대해 TMDB 검색·후보 선택만 수행한다(파일 행·DB 갱신 없음).

    Args:
        group_key: 그룹 식별 키.
        provider: 메타데이터 검색 포트.
        root_id: DB 단축 경로용 루트 id.
        representative_path_norm: 그룹 대표 path_norm.
        title_match: TMDB 매칭 저장소.
        title_groups: 작품 그룹 저장소.

    Returns:
        (그룹 결과 DTO, 적용할 후보 또는 None).
    """
    raw_candidates = _search_series_candidates_for_group(
        group_key,
        provider,
        root_id=root_id,
        representative_path_norm=representative_path_norm,
        title_match=title_match,
        title_groups=title_groups,
    )
    best, conf, reason = _select_best_candidate(raw_candidates, group_key, "")

    if best is None or not best.tmdb_id:
        return (
            GroupMatchResultDTO(
                group_key=group_key,
                matched=False,
                tmdb_id=None,
                korean_group_title="",
                original_title="",
                confidence=0.0,
                reason=reason,
            ),
            None,
        )

    korean = (best.name_ko or "").strip()
    original = (best.original_name or "").strip()
    dto = GroupMatchResultDTO(
        group_key=group_key,
        matched=bool(korean),
        tmdb_id=best.tmdb_id,
        korean_group_title=korean,
        original_title=original,
        confidence=conf,
        reason=reason,
    )
    return dto, best


def _match_single_group_apply_persist(
    files: list[MatchFileRow],
    _group_key: str,
    indices: list[int],
    best: TmdbSeriesCandidateDTO,
    conf: float,
    *,
    root_id: int | None = None,
    representative_path_norm: str | None = None,
    title_match: TitleMatchRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
) -> None:
    """선택된 후보로 파일 행·그룹 매칭 DB를 갱신한다.

    Args:
        files: 전체 파일 행(제자리 수정).
        _group_key: 그룹 식별 키(시그니처 호환·로깅은 gid 사용).
        indices: 그룹 행 인덱스.
        best: 선택된 시리즈 후보.
        conf: 매칭 점수(0~1).
        root_id: DB 영속화용 루트 id.
        representative_path_norm: 그룹 대표 path_norm.
        title_match: TMDB 매칭 저장소.
        title_groups: 작품 그룹 저장소.

    Returns:
        None.
    """
    apply_tmdb_candidate_to_file_rows(files, indices, best)

    if (
        root_id is not None
        and representative_path_norm
        and title_match is not None
        and title_groups is not None
    ):
        gid = title_groups.get_group_id_for_path_norm(root_id, representative_path_norm)
        if gid is not None:
            raw_json = json.dumps(asdict(best), ensure_ascii=False, separators=(",", ":"))
            exp = _utc_plus_days_iso_z(7)
            try:
                title_match.upsert_series(best, raw_json=raw_json, expires_at=exp)
                existing = title_match.get_group_match(gid)
                preserve_confirmed = (
                    existing is not None
                    and existing.match_status == "confirmed"
                    and int(existing.tmdb_id) == int(best.tmdb_id)
                )
                if not preserve_confirmed:
                    title_match.set_group_match(
                        gid,
                        int(best.tmdb_id),
                        "auto_matched",
                        conf,
                    )
            except Exception:
                logger.exception(
                    "group TMDB persist 실패 group_id=%s tmdb_id=%s",
                    gid,
                    best.tmdb_id,
                )


def _match_single_group(
    files: list[MatchFileRow],
    group_key: str,
    indices: list[int],
    provider: MetadataProvider,
    *,
    root_id: int | None = None,
    representative_path_norm: str | None = None,
    title_match: TitleMatchRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
) -> GroupMatchResultDTO:
    """한 그룹에 대해 TMDB 검색·선택 후 파일 행과 그룹 결과를 만든다.

    Args:
        files: 전체 파일 행 목록(성공 시 제자리 수정).
        group_key: 그룹 식별 키.
        indices: 그룹에 속한 행 인덱스.
        provider: 메타데이터 검색 포트.
        root_id: DB 영속화용 루트 id.
        representative_path_norm: 그룹 대표 경로 키.
        title_match: TMDB 매칭 저장소.
        title_groups: 작품 그룹 저장소.

    Returns:
        해당 그룹의 매칭 결과 DTO.
    """
    dto, cand = _match_single_group_search_phase(
        group_key,
        provider,
        root_id=root_id,
        representative_path_norm=representative_path_norm,
        title_match=title_match,
        title_groups=title_groups,
    )
    if cand is not None:
        _match_single_group_apply_persist(
            files,
            group_key,
            indices,
            cand,
            dto.confidence,
            root_id=root_id,
            representative_path_norm=representative_path_norm,
            title_match=title_match,
            title_groups=title_groups,
        )
    return dto


def _representative_path_norm_for_group(
    files: list[MatchFileRow],
    root_scope: int | None,
    indices: list[int],
) -> str | None:
    """스캔 루트 스코프가 있을 때 그룹 대표 파일의 정규화 경로 키를 만든다.

    Args:
        files: 전체 파일 행 목록.
        root_scope: 인덱스 루트 ID. None이면 경로 키를 만들지 않음.
        indices: 그룹에 속한 행 인덱스 목록.

    Returns:
        정규화 경로 키. 스코프 없음·빈 그룹·경로 오류 시 None.
    """
    if root_scope is None or not indices:
        return None
    try:
        return normalize_path_key(files[indices[0]].original_file)
    except OSError:
        return None


def _match_max_workers() -> int:
    """병렬 그룹 매칭 스레드 상한을 반환한다.

    Args:
        없음.

    Returns:
        1 이상 8 이하 정수.
    """
    try:
        w = int(os.environ.get("ANIVAULT_MATCH_MAX_WORKERS", "4"))
    except ValueError:
        w = 4
    return max(1, min(8, w))


def _search_one_group_for_parallel(
    files: list[MatchFileRow],
    entry: tuple[str, list[int]],
    *,
    provider: MetadataProvider,
    root_scope: int | None,
    cancel_token: Event,
    title_match: TitleMatchRepository | None,
    title_groups: TitleGroupRepository | None,
) -> tuple[str, list[int], str | None, GroupMatchResultDTO, TmdbSeriesCandidateDTO | None]:
    """워커 스레드에서 단일 그룹 검색·후보 선택을 수행한다.

    Args:
        files: 전체 파일 행(경로 정규화만 읽음).
        entry: (그룹 키, 행 인덱스 목록).
        provider: 메타데이터 검색 포트.
        root_scope: 라이브러리 루트 ID.
        cancel_token: 설정 시 취소 결과 DTO만 반환.
        title_match: TMDB 매칭 저장소.
        title_groups: title_groups 포트.

    Returns:
        (그룹 키, 인덱스, 대표 path_norm, DTO, 후보).
    """
    key, indices = entry
    path_norm = _representative_path_norm_for_group(files, root_scope, indices)
    if cancel_token.is_set():
        return (
            key,
            indices,
            path_norm,
            GroupMatchResultDTO(
                group_key=key,
                matched=False,
                tmdb_id=None,
                korean_group_title="",
                original_title="",
                confidence=0.0,
                reason="cancelled",
            ),
            None,
        )
    dto, cand = _match_single_group_search_phase(
        key,
        provider,
        root_id=root_scope,
        representative_path_norm=path_norm,
        title_match=title_match,
        title_groups=title_groups,
    )
    return key, indices, path_norm, dto, cand


def _collect_group_match_results(
    files: list[MatchFileRow],
    key_to_indices: dict[str, list[int]],
    *,
    provider: MetadataProvider,
    root_scope: int | None,
    progress_callback: MatchProgressCallback | None,
    cancel_token: Event,
    title_match: TitleMatchRepository | None,
    title_groups: TitleGroupRepository | None,
) -> list[GroupMatchResultDTO]:
    """그룹 키 순서대로 TMDB 매칭을 수행하고 결과 DTO 목록을 만든다.

    Args:
        files: 전체 파일 행(제자리 갱신).
        key_to_indices: 그룹 키 → 행 인덱스 목록.
        provider: 메타데이터 검색 포트.
        root_scope: 인덱스 루트 ID(경로 대표 키용).
        progress_callback: 진행 이벤트 콜백.
        cancel_token: 설정 시 루프 중단.
        title_match: TMDB·그룹 매칭 저장소.
        title_groups: title_groups 조회 포트.

    Returns:
        그룹별 매칭 결과 DTO 리스트(중단 시 이때까지 누적).
    """
    items = list(key_to_indices.items())
    total = len(items)
    _notify_match_progress_prepare(progress_callback, total)
    group_results: list[GroupMatchResultDTO] = []
    if not total:
        return group_results

    workers = _match_max_workers()
    if workers <= 1:
        ordered: list[
            tuple[str, list[int], str | None, GroupMatchResultDTO, TmdbSeriesCandidateDTO | None]
        ] = []
        for key, indices in items:
            ordered.append(
                _search_one_group_for_parallel(
                    files,
                    (key, indices),
                    provider=provider,
                    root_scope=root_scope,
                    cancel_token=cancel_token,
                    title_match=title_match,
                    title_groups=title_groups,
                ),
            )
    else:

        def _parallel_entry(
            entry: tuple[str, list[int]],
        ) -> tuple[
            str,
            list[int],
            str | None,
            GroupMatchResultDTO,
            TmdbSeriesCandidateDTO | None,
        ]:
            """단일 그룹 검색 태스크 어댑터.

            Args:
                entry: (그룹 키, 인덱스 목록).

            Returns:
                `_search_one_group_for_parallel`와 동일 튜플.
            """
            return _search_one_group_for_parallel(
                files,
                entry,
                provider=provider,
                root_scope=root_scope,
                cancel_token=cancel_token,
                title_match=title_match,
                title_groups=title_groups,
            )

        with ThreadPoolExecutor(max_workers=workers) as pool:
            ordered = list(pool.map(_parallel_entry, items))

    for n, (key, indices, path_norm, dto, cand) in enumerate(ordered):
        if cancel_token.is_set():
            break
        _notify_match_progress_step(
            progress_callback,
            total,
            n + 1,
            f"TMDB 검색 ({n + 1}/{total}): {key[:60]}",
        )
        if cand is not None:
            _match_single_group_apply_persist(
                files,
                key,
                indices,
                cand,
                dto.confidence,
                root_id=root_scope,
                representative_path_norm=path_norm,
                title_match=title_match,
                title_groups=title_groups,
            )
        group_results.append(dto)
    return group_results


def make_execute(
    provider: MetadataProvider,
    *,
    title_match: TitleMatchRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
    poster_sync: Callable[[MatchResult], None] | None = None,
) -> Callable[[MatchInput, MatchProgressCallback | None, Event], MatchResult]:
    """MetadataProvider가 주입된 매칭 실행 함수를 만든다.

    Args:
        provider: 메타데이터 검색 포트.
        title_match: TMDB 캐시·그룹 매칭 저장소.
        title_groups: title_groups 조회.
        poster_sync: 매칭 직후 로컬 포스터 동기화. None이면 생략.

    Returns:
        (MatchInput, progress_callback, cancel_token) -> MatchResult 클로저.
    """

    def execute(
        input_dto: MatchInput,
        progress_callback: MatchProgressCallback | None,
        cancel_token: Event,
    ) -> MatchResult:
        """그룹별로 TMDB 검색 후 파일 행을 갱신한다.

        Args:
            input_dto: 매칭 입력(파일 행 튜플).
            progress_callback: ProgressEvent를 받는 콜백. None이면 진행 보고 없음.
            cancel_token: 설정 시 중단.

        Returns:
            갱신된 파일 행과 그룹별 매칭 결과.
        """
        files = list(input_dto.files)
        if cancel_token.is_set():
            return MatchResult(files=tuple(files), groups=())

        key_to_indices = _index_files_by_group_key(files)
        group_results = _collect_group_match_results(
            files,
            key_to_indices,
            provider=provider,
            root_scope=input_dto.index_root_id,
            progress_callback=progress_callback,
            cancel_token=cancel_token,
            title_match=title_match,
            title_groups=title_groups,
        )

        result = MatchResult(files=tuple(files), groups=tuple(group_results))
        if poster_sync is not None:
            poster_sync(result)
        return result

    return execute
