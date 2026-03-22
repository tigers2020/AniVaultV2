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
from anivault.domain.rules.tmdb_search_query import (
    iter_strip_last_word_chain,
    iter_tmdb_search_queries,
)

_MAX_CANDIDATES = 5

MatchProgressCallback = Callable[[ProgressEvent], None]


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
    qn = _normalize_key(query)
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
    poster = _poster_url(poster_path_raw)
    backdrop_path_raw = (candidate.backdrop_path or "").strip()
    backdrop = _backdrop_url(backdrop_path_raw)
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


def _search_series_candidates_for_group(
    group_key: str,
    provider: MetadataProvider,
) -> list[TmdbSeriesCandidateDTO]:
    """그룹 키에 대해 변형 검색어·끝단어 제거 체인으로 TMDB 후보를 찾는다.

    연도 필터는 쓰지 않는다(파일 연도와 TMDB 첫 방영 연도 불일치로 0건이 나오는 것을 피함).

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


def _match_single_group(
    files: list[MatchFileRow],
    group_key: str,
    indices: list[int],
    provider: MetadataProvider,
) -> GroupMatchResultDTO:
    """한 그룹에 대해 TMDB 검색·선택 후 파일 행과 그룹 결과를 만든다.

    Args:
        files: 전체 파일 행 목록(성공 시 제자리 수정).
        group_key: 그룹 식별 키.
        indices: 그룹에 속한 행 인덱스.
        provider: 메타데이터 검색 포트.

    Returns:
        해당 그룹의 매칭 결과 DTO.
    """
    raw_candidates = _search_series_candidates_for_group(group_key, provider)
    best, conf, reason = _select_best_candidate(raw_candidates, group_key, "")

    if best is None or not best.tmdb_id:
        return GroupMatchResultDTO(
            group_key=group_key,
            matched=False,
            tmdb_id=None,
            korean_group_title="",
            original_title="",
            confidence=0.0,
            reason=reason,
        )

    korean = (best.name_ko or "").strip()
    original = (best.original_name or "").strip()
    apply_tmdb_candidate_to_file_rows(files, indices, best)

    return GroupMatchResultDTO(
        group_key=group_key,
        matched=bool(korean),
        tmdb_id=best.tmdb_id,
        korean_group_title=korean,
        original_title=original,
        confidence=conf,
        reason=reason,
    )


def make_execute(
    provider: MetadataProvider,
) -> Callable[[MatchInput, MatchProgressCallback | None, Event], MatchResult]:
    """MetadataProvider가 주입된 매칭 실행 함수를 만든다.

    Args:
        provider: 메타데이터 검색 포트.

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
        total = len(key_to_indices)
        group_results: list[GroupMatchResultDTO] = []

        _notify_match_progress_prepare(progress_callback, total)

        for n, (key, indices) in enumerate(key_to_indices.items()):
            if cancel_token.is_set():
                break
            _notify_match_progress_step(
                progress_callback,
                total,
                n + 1,
                f"TMDB 검색 ({n + 1}/{total}): {key[:60]}",
            )
            group_results.append(_match_single_group(files, key, indices, provider))

        return MatchResult(files=tuple(files), groups=tuple(group_results))

    return execute
