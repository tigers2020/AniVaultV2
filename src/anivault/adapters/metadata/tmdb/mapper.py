"""mapper.py

tmdbapis 응답 객체를 애플리케이션 TmdbSeriesCandidateDTO로 변환한다.

Author: Pom Kim
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from anivault.contracts.tmdb import (
    SearchTvLibraryRecord,
    TmdbSeriesCandidate,
    TvSeasonEpisodeInfo,
    TvSeasonOverview,
)


def _as_str(value: Any) -> str:
    """값을 표시용 문자열로 만든다. 언어 객체는 iso_639_1을 쓴다.

    Args:
        value: 임의 객체 또는 None.

    Returns:
        문자열. None이면 빈 문자열.
    """
    if value is None:
        return ""
    if hasattr(value, "iso_639_1"):
        raw = getattr(value, "iso_639_1", None)
        return str(raw) if raw is not None else ""
    return str(value)


def _first_air_date_str(tv: Any) -> str:
    """TVShow의 first_air_date를 YYYY-MM-DD 문자열로 만든다.

    Args:
        tv: tmdbapis TVShow 유사 객체.

    Returns:
        날짜 문자열. 없으면 빈 문자열.
    """
    raw = getattr(tv, "first_air_date", None)
    if raw is None:
        return ""
    if isinstance(raw, (date, datetime)):
        return raw.strftime("%Y-%m-%d")
    return str(raw)


def tv_show_to_candidate(tv: Any) -> TmdbSeriesCandidate:
    """tmdbapis TVShow(검색 결과 포함)에서 DTO를 만든다.

    Args:
        tv: TVShow 유사 객체.

    Returns:
        TmdbSeriesCandidateDTO. id 변환 실패 시 tmdb_id 0 등 기본값.
    """
    tid_raw = getattr(tv, "id", 0)
    try:
        tmdb_id = int(tid_raw)
    except (TypeError, ValueError):
        tmdb_id = 0

    pop_raw = getattr(tv, "popularity", 0) or 0
    try:
        popularity = float(pop_raw)
    except (TypeError, ValueError):
        popularity = 0.0

    poster = getattr(tv, "poster_path", None)
    poster_path = str(poster) if poster else ""

    backdrop = getattr(tv, "backdrop_path", None)
    backdrop_path = str(backdrop) if backdrop else ""

    return TmdbSeriesCandidate(
        tmdb_id=tmdb_id,
        name_ko=_as_str(getattr(tv, "name", None) or getattr(tv, "title", None)),
        original_name=_as_str(getattr(tv, "original_name", None)),
        first_air_date=_first_air_date_str(tv),
        original_language=_as_str(getattr(tv, "original_language", None)),
        overview=_as_str(getattr(tv, "overview", None)),
        poster_path=poster_path,
        backdrop_path=backdrop_path,
        popularity=popularity,
    )


def _country_code_item(c: Any) -> str:
    if isinstance(c, str):
        return c
    raw = getattr(c, "iso_3166_1", None)
    if raw is not None:
        return str(raw)
    return str(c) if c is not None else ""


def tv_show_to_search_tv_library_record(tv: Any, language: str) -> SearchTvLibraryRecord:
    """tmdbapis TVShow(검색 결과)를 픽스처 `results[]` 정렬 라이브러리 행으로 만든다."""
    tid_raw = getattr(tv, "id", 0)
    try:
        tmdb_id = int(tid_raw)
    except (TypeError, ValueError):
        tmdb_id = 0

    adult = bool(getattr(tv, "adult", False))

    bp = getattr(tv, "backdrop_path", None)
    backdrop_path = str(bp) if bp else None

    pp = getattr(tv, "poster_path", None)
    poster_path = str(pp) if pp else None

    gids = getattr(tv, "genre_ids", None)
    if gids is None:
        genre_ids_json = "[]"
    else:
        genre_ids_json = json.dumps([int(x) for x in gids], separators=(",", ":"))

    oc = getattr(tv, "origin_country", None)
    if oc is None:
        origin_country_json = "[]"
    else:
        origin_country_json = json.dumps(
            [_country_code_item(c) for c in oc],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    pop_raw = getattr(tv, "popularity", 0) or 0
    try:
        popularity = float(pop_raw)
    except (TypeError, ValueError):
        popularity = 0.0

    va_raw = getattr(tv, "vote_average", 0) or 0
    try:
        vote_average = float(va_raw)
    except (TypeError, ValueError):
        vote_average = 0.0

    vc_raw = getattr(tv, "vote_count", 0) or 0
    try:
        vote_count = int(vc_raw)
    except (TypeError, ValueError):
        vote_count = 0

    lang = (language or "").strip()
    return SearchTvLibraryRecord(
        tmdb_id=tmdb_id,
        language=lang,
        adult=adult,
        backdrop_path=backdrop_path,
        genre_ids_json=genre_ids_json,
        origin_country_json=origin_country_json,
        original_language=_as_str(getattr(tv, "original_language", None)),
        original_name=_as_str(getattr(tv, "original_name", None)),
        overview=_as_str(getattr(tv, "overview", None)),
        popularity=popularity,
        poster_path=poster_path,
        first_air_date=_first_air_date_str(tv),
        name=_as_str(getattr(tv, "name", None) or getattr(tv, "title", None)),
        vote_average=vote_average,
        vote_count=vote_count,
    )


def season_to_overview(season: Any) -> TvSeasonOverview:
    """Map a tmdbapis Season-like object to a normalized overview DTO."""

    raw_episodes = getattr(season, "episodes", None) or []
    season_number_raw = getattr(season, "season_number", 0)
    try:
        season_number = int(season_number_raw)
    except (TypeError, ValueError):
        season_number = 0
    episodes: list[TvSeasonEpisodeInfo] = []
    for episode in raw_episodes:
        number_raw = getattr(episode, "episode_number", 0)
        try:
            number = int(number_raw)
        except (TypeError, ValueError):
            continue
        if number <= 0:
            continue
        episodes.append(
            TvSeasonEpisodeInfo(
                number=number,
                name=_as_str(getattr(episode, "name", None) or getattr(episode, "title", None)),
                still_url=_as_str(getattr(episode, "still_url", None)),
            )
        )
    episodes.sort(key=lambda item: item.number)
    return TvSeasonOverview(season_number=season_number, episodes=tuple(episodes))
