"""match_series.py

파싱된 파일 그룹을 TMDB TV 시리즈에 매칭하고 한글 표시 제목을 채운다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable
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

_MAX_CANDIDATES = 5


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


def _normalize_key(s: str) -> str:
    """비교용 키: 공백 제거 후 소문자만 남긴다.

    Args:
        s: 원본 문자열.

    Returns:
        정규화된 키.
    """
    return "".join(c.lower() for c in s if not c.isspace())


def _year_prefix(iso_date: str) -> str:
    """ISO 날짜 문자열에서 연도 4자리 접두를 반환한다.

    Args:
        iso_date: YYYY-MM-DD 형태 등.

    Returns:
        앞 4자리(연도). 길이 부족 시 빈 문자열.
    """
    d = (iso_date or "").strip()
    return d[:4] if len(d) >= 4 else ""


def _poster_url(poster_path: str) -> str:
    """TMDB poster_path를 전체 URL로 만든다.

    Args:
        poster_path: API 상대 경로 또는 이미 절대 URL.

    Returns:
        이미지 URL. 비어 있으면 빈 문자열.
    """
    p = (poster_path or "").strip()
    if not p:
        return ""
    if p.startswith("http"):
        return p
    return f"https://image.tmdb.org/t/p/w342{p}"


def _backdrop_url(backdrop_path: str) -> str:
    """TMDB backdrop_path를 전체 URL로 만든다.

    Args:
        backdrop_path: API 상대 경로 또는 이미 절대 URL.

    Returns:
        이미지 URL. 비어 있으면 빈 문자열.
    """
    p = (backdrop_path or "").strip()
    if not p:
        return ""
    if p.startswith("http"):
        return p
    return f"https://image.tmdb.org/t/p/w780{p}"


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
    qn = _normalize_key(query)
    best: TmdbSeriesCandidateDTO | None = None
    best_score = -1.0
    reason = "fallback_first"
    for c in candidates[:_MAX_CANDIDATES]:
        score = 0.0
        names = [_normalize_key(c.name_ko), _normalize_key(c.original_name)]
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
        if score > best_score:
            best_score = score
            best = c
    if best is None:
        return candidates[0], 0.5, "first_result"
    conf = min(1.0, max(0.0, best_score / 15.0))
    return best, conf, reason


def _rep_year_for_indices(files: list[MatchFileRow], indices: list[int]) -> str:
    """인덱스 목록에서 첫 숫자 연도 문자열을 찾는다.

    Args:
        files: 전체 파일 행 목록.
        indices: 같은 그룹에 속한 인덱스.

    Returns:
        숫자만 있는 year 필드. 없으면 빈 문자열.
    """
    for i in indices:
        y = (files[i].year or "").strip()
        if y.isdigit():
            return y
    return ""


def make_execute(
    provider: MetadataProvider,
) -> Callable[[MatchInput, object, Event], MatchResult]:
    """MetadataProvider가 주입된 매칭 실행 함수를 만든다.

    Args:
        provider: 메타데이터 검색 포트.

    Returns:
        (MatchInput, progress_callback, cancel_token) -> MatchResult 클로저.
    """

    def execute(
        input_dto: MatchInput,
        progress_callback: object,
        cancel_token: Event,
    ) -> MatchResult:
        """그룹별로 TMDB 검색 후 파일 행을 갱신한다.

        Args:
            input_dto: 매칭 입력(파일 행 튜플).
            progress_callback: ProgressEvent를 받는 콜백. 없으면 무시.
            cancel_token: 설정 시 중단.

        Returns:
            갱신된 파일 행과 그룹별 매칭 결과.
        """
        files = list(input_dto.files)
        if cancel_token.is_set():
            return MatchResult(files=tuple(files), groups=())

        key_to_indices: dict[str, list[int]] = {}
        for i, f in enumerate(files):
            key_to_indices.setdefault(_group_key(f), []).append(i)
        total = len(key_to_indices)
        group_results: list[GroupMatchResultDTO] = []

        if callable(progress_callback) and total:
            progress_callback(
                ProgressEvent(
                    stage="match",
                    current=0,
                    total=total,
                    message="TMDB 매칭 준비…",
                    percent=0,
                )
            )

        for n, (key, indices) in enumerate(key_to_indices.items()):
            if cancel_token.is_set():
                break
            if callable(progress_callback) and total:
                pct = int((n + 1) * 100 / total) if total else 100
                progress_callback(
                    ProgressEvent(
                        stage="match",
                        current=n + 1,
                        total=total,
                        message=f"TMDB 검색 ({n + 1}/{total}): {key[:60]}",
                        percent=pct,
                    )
                )

            year_str = _rep_year_for_indices(files, indices)
            year_i = int(year_str) if year_str.isdigit() else None
            raw_candidates = list(provider.search_series(key, year=year_i))
            best, conf, reason = _select_best_candidate(raw_candidates, key, year_str)

            if best is None or not best.tmdb_id:
                group_results.append(
                    GroupMatchResultDTO(
                        group_key=key,
                        matched=False,
                        tmdb_id=None,
                        korean_group_title="",
                        original_title="",
                        confidence=0.0,
                        reason=reason,
                    )
                )
                continue

            korean = (best.name_ko or "").strip()
            original = (best.original_name or "").strip()
            poster_path_raw = (best.poster_path or "").strip()
            poster = _poster_url(poster_path_raw)
            backdrop_path_raw = (best.backdrop_path or "").strip()
            backdrop = _backdrop_url(backdrop_path_raw)
            tid = str(best.tmdb_id)
            tmdb_year = _year_prefix(best.first_air_date)

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
                )

            group_results.append(
                GroupMatchResultDTO(
                    group_key=key,
                    matched=bool(korean),
                    tmdb_id=best.tmdb_id,
                    korean_group_title=korean,
                    original_title=original,
                    confidence=conf,
                    reason=reason,
                )
            )

        return MatchResult(files=tuple(files), groups=tuple(group_results))

    return execute
