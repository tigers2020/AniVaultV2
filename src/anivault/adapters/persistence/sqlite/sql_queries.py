"""sql_queries.py

SQLite 저장소 간 공유 SQL 문자열.

Author: Pom Kim
"""

# group_tmdb_matches: 그룹당 단일 TMDB 매칭 행 upsert (저장소 간 문장 동기화용).
GROUP_TMDB_MATCH_UPSERT_SQL = """
INSERT INTO group_tmdb_matches (
    group_id, tmdb_id, match_status, match_score, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(group_id) DO UPDATE SET
    tmdb_id = excluded.tmdb_id,
    match_status = excluded.match_status,
    match_score = excluded.match_score,
    updated_at = excluded.updated_at
"""
